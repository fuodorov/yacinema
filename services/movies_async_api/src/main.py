import uvicorn

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

app = FastAPI(
    title="Movies Async API",
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    default_response_class=ORJSONResponse,
)


@app.get("/api/hello")
def read_root():
    return {"Hello": "World"}


if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8000,
        reload=True,
        debug=True,
    )
