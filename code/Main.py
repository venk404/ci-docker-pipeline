from fastapi import FastAPI, HTTPException
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from db_students import insertstudent, get_all_students
from db_students import get_student_by_Id, Update_student, delete_student
import uvicorn
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from typing import Optional
from dotenv import load_dotenv
import os
import json
from loguru import logger
import sys
import time
import psycopg2
from prometheus_client import Counter, Histogram


# Configure Loguru to emit JSON logs
def serialize(record):
    subset = {
        "timestamp": record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "message": record["message"],
        "level": record["level"].name,
        "function": record["function"],
        "line": record["line"],
        "file": record["file"].name,
        "module": record["module"]
    }
    return json.dumps(subset)


def patching(record):
    record["extra"]["serialized"] = serialize(record)


logger.remove()
logger = logger.patch(patching)
logger.add(sys.stderr, format="{extra[serialized]}", backtrace=True)

load_dotenv()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['endpoint', 'method', 'status_code']
)
REQUEST_LATENCY = Histogram(
    'api_request_latency_seconds',
    'API request latency in seconds',
    ['endpoint', 'method', 'status_code'],
    buckets=[0.1, 0.3, 0.5, 1.0, 2.0, 5.0, 10.0]
)
ERROR_COUNT = Counter(
    'api_errors_total',
    'Total number of API errors',
    ['endpoint', 'method', 'status_code']
)


class Student(BaseModel):
    name: str = Field(examples=["Ganesh Gaitonde"])
    email: EmailStr = Field(examples=["Gopalmate@gmail.com"])
    age: int = Field(examples=[22])
    phone: str = Field(pattern=r'^\d{10}$', min_length=10, max_length=10,
                       examples=[1234567890])

    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            'examples': [
                {
                    "name": "Ganesh Gaitonde",
                    "email": "Gopalmat@gmail.com",
                    "age": 11,
                    "phone": "1234567890"
                }
            ]
        }
    )


class UpdateStudent(BaseModel):
    name: Optional[str] = Field(default=None, examples=["Ganesh Gaitonde"])
    email: Optional[EmailStr] = Field(default=None,
                                      examples=["Gopalmate@gmail.com"])
    age: Optional[int] = Field(default=None, examples=[22])
    phone: Optional[str] = Field(default=None, pattern=r'^\d{10}$',
                                 min_length=10,
                                 max_length=10, examples=[1234567890])

    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            'examples': [
                {
                    "name": "Ganesh Gaitonde",
                    "email": "Gopalmate@gmail.com",
                    "age": 22,
                    "phone": "1234567890"
                }
            ]
        }
    )


app = FastAPI()
app.start_time = time.time()

version_v1 = APIRouter()
version_v2 = APIRouter()


# Middleware to capture metrics
@app.middleware("http")
async def prometheus_metrics(request: Request, call_next):
    """
    Middleware to capture request count, latency, and errors for Prometheus.
    """
    endpoint = request.url.path
    method = request.method
    start_time = time.time()
    try:
        response = await call_next(request)
        status_code = response.status_code
        REQUEST_COUNT.labels(endpoint=endpoint, method=method,
                             status_code=status_code).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint, method=method,
                               status_code=status_code
                               ).observe(time.time() - start_time)
        if status_code >= 400:
            ERROR_COUNT.labels(endpoint=endpoint, method=method,
                               status_code=status_code).inc()
        return response
    except Exception as e:
        ERROR_COUNT.labels(endpoint=endpoint, method=method,
                           status_code=500).inc()
        raise e


# Middleware to catch malformed JSON
@app.middleware("http")
async def handle_malformed_json(request: Request, call_next):
    """
    Middleware to catch malformed JSON in the request body.
    """
    if request.headers.get("content-type") == "application/json":
        try:
            await request.json()  # Try parsing the JSON body
        except json.JSONDecodeError as e:
            return JSONResponse(
                status_code=400,
                content={
                    "error": """Given Json is not well formatted,
                                please check the input Json""",
                    "details": str(e),
                },
            )
    return await call_next(request)


# Custom handler for 422 Unprocessable Entity
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    error_messages = []
    for error in exc.errors():
        loc = " -> ".join(str(i) for i in error["loc"])
        msg = error["msg"]
        type_error = error["type"]

        if type_error == "value_error.number.not_a_number":
            msg = "The value provided is not a valid number. Check the input."
        elif type_error.startswith("type_error"):
            msg = f"""Invalid type for {loc}.
                       Expected a valid {type_error.split('.')[-1]}."""

        error_messages.append(f"{loc}: {msg}")

    logger.error({
        "level": "error",
        "event": "validation_error",
        "endpoint": request.url.path,
        "method": request.method,
        "error": error_messages
    })
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed for the input data.",
            "details": error_messages,
        },
    )


@version_v1.post("/AddStudent", status_code=200)
async def create_student(student: Student) -> Student:
    try:
        logger.info({
            "event": "create_student_start",
            "endpoint": "/AddStudent",
            "method": "POST"
        })
        res = jsonable_encoder(insertstudent(data=student))
        if res['status'] == "success":
            logger.info({
                "event": "create_student_success",
                "endpoint": "/AddStudent",
                "method": "POST"
            })
            return JSONResponse(content={"message": "Student data added",
                                         "student_id": res["student_id"]})
        else:
            logger.error({
                "event": "create_student_failure",
                "endpoint": "/AddStudent",
                "method": "POST",
                "error": res['message']
            })
            raise HTTPException(status_code=400, detail=res['message'])
    except Exception as e:
        logger.error({
            "event": "create_student_error",
            "endpoint": "/AddStudent",
            "method": "POST",
            "error": str(e)
        })
        return JSONResponse(status_code=400, content=str(e))


@version_v1.get("/GetAllStudents", status_code=200)
async def get_students() -> dict:
    try:
        logger.info({
            "event": "get_all_students_start",
            "endpoint": "/GetAllStudents",
            "method": "GET"
        })
        res = jsonable_encoder(get_all_students())
        if res['status'] == "success":
            logger.info({
                "event": "get_all_students_success",
                "endpoint": "/GetAllStudents",
                "method": "GET",
                "student_count": len(res['students'])
            })
            return JSONResponse(content=res['students'])
        else:
            logger.error({
                "event": "get_all_students_failure",
                "endpoint": "/GetAllStudents",
                "method": "GET",
                "error": res['message']
            })
            return JSONResponse(status_code=400,
                                content={"detail": res['message']})
    except Exception as e:
        logger.error({
            "event": "get_all_students_error",
            "endpoint": "/GetAllStudents",
            "method": "GET",
            "error": str(e)
        })
        return JSONResponse(status_code=400, content=str(e))


@version_v1.get("/GetStudent", status_code=200)
async def get_student(id: int) -> dict:
    try:
        logger.info({
            "event": "get_student_start",
            "endpoint": "/GetStudent",
            "method": "GET"
        })
        res = get_student_by_Id(id)
        if res['status'] == "success":
            logger.info({
                "event": "get_student_success",
                "endpoint": "/GetStudent",
                "method": "GET"
            })
            return JSONResponse(content=res['students'])
        else:
            logger.error({
                "event": "get_student_failure",
                "endpoint": "/GetStudent",
                "method": "GET",
                "error": res['message']
            })
            return JSONResponse(status_code=400,
                                content={"detail": res['message']})
    except Exception as e:
        logger.error({
            "event": "get_student_error",
            "endpoint": "/GetStudent",
            "method": "GET",
            "error": str(e)
        })
        return JSONResponse(status_code=400, content=str(e))


@version_v2.patch("/UpdateStudent", status_code=200)
async def Update(id: int, student: UpdateStudent) -> dict:
    try:
        logger.info({
            "event": "update_student_start",
            "endpoint": "/UpdateStudent",
            "method": "PATCH"
        })
        res = Update_student(id, student)
        if res['status'] == "success":
            logger.info({
                "event": "update_student_success",
                "endpoint": "/UpdateStudent",
                "method": "PATCH"
            })
            return JSONResponse(content={"message": res["message"]})
        else:
            logger.error({
                "event": "update_student_failure",
                "endpoint": "/UpdateStudent",
                "method": "PATCH",
                "error": res['message']
            })
            raise HTTPException(
                status_code=400,
                detail=res['message']
            )
    except Exception as e:
        logger.error({
            "event": "update_student_error",
            "endpoint": "/UpdateStudent",
            "method": "PATCH",
            "error": str(e)
        })
        return JSONResponse(status_code=500, content={"detail": str(e)})


@version_v2.delete("/DeleteStudent", status_code=200)
async def delete(id: int) -> dict:
    try:
        logger.info({
            "event": "delete_student_start",
            "endpoint": "/DeleteStudent",
            "method": "DELETE"
        })
        res = delete_student(id)
        if res['status'] == "success":
            logger.info({
                "event": "delete_student_success",
                "endpoint": "/DeleteStudent",
                "method": "DELETE"
            })
            return JSONResponse(content={"message": res["message"]})
        else:
            logger.error({
                "event": "delete_student_failure",
                "endpoint": "/DeleteStudent",
                "method": "DELETE",
                "error": res['message']
            })
            raise HTTPException(
                status_code=400,
                detail=res['message']
            )
    except Exception as e:
        logger.error({
            "event": "delete_student_error",
            "endpoint": "/DeleteStudent",
            "method": "DELETE",
            "error": str(e)
        })
        return JSONResponse(status_code=500, content={"detail": str(e)})


@version_v1.get("/HealthCheck", status_code=200)
async def HealthCheck() -> dict:
    """
    Performs a comprehensive health check on critical components.
    Returns status of database connectivity and application uptime.
    """
    health_status = {
        "status": "healthy",
        "components": {
            "database": {"status": "unknown", "details": ""},
            "application": {"status": "up",
                            "uptime_seconds":
                            int(time.time() - app.start_time)}
        }
    }

    # Check database connectivity
    try:
        conn = psycopg2.connect(
            database=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
        )
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
        conn.close()
        health_status["components"]["database"]["status"] = "healthy"
        return JSONResponse(status_code=200, content=health_status)
    except psycopg2.Error as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["database"]["status"] = "unhealthy"
        health_status["components"]["database"]["details"] = str(e)
        logger.error({
            "event": "health_check_db_error",
            "endpoint": "/HealthCheck",
            "method": "GET",
            "error": str(e)
        })
        return JSONResponse(status_code=503, content=health_status)


# Expose Prometheus metrics endpoint
@app.get("/metrics", include_in_schema=False)
async def metrics():
    """
    Expose Prometheus metrics for scraping.
    """
    from prometheus_client import generate_latest
    return Response(content=generate_latest(), media_type="text/plain")


app.include_router(version_v1, tags=['Version 1 Api Endpoints'])
app.include_router(version_v2, prefix='/v2', tags=['Version 2 Api Endpoints'])

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
