"""Test receiver server."""

import json

from fastapi import FastAPI, Request

app = FastAPI()


@app.post("/")
async def handle_post_request(request: Request) -> None:
    """Handle wehook response."""
    data = await request.json()

    with open("res.json", "w") as f:
        f.write(json.dumps(data))

    assert isinstance(data, dict)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7654)
