from fastapi import APIRouter, Query
from starlette.responses import HTMLResponse

router = APIRouter(prefix="/instajoin")


@router.get("", response_class=HTMLResponse, include_in_schema=False)
async def play(code: str = Query(...)):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Card Games Spiel beitreten</title>
        <link rel="icon" href="/static/icon.png">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f0f0f0;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }}
            .container {{
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                padding: 40px;
                text-align: center;
                width: 90%;
                max-width: 500px;
            }}
            .logo {{
                width: 150px;
                margin-bottom: 20px;
            }}
            h1 {{
                margin-bottom: 30px;
            }}
            .join-button {{
                display: inline-block;
                padding: 15px 30px;
                font-size: 18px;
                text-decoration: none;
                background-color: #7A73D1;
                color: #fff;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .download-buttons a {{
                display: inline-block;
                padding: 10px 20px;
                font-size: 14px;
                text-decoration: none;
                background-color: #8d8d8d;
                color: #fff;
                border-radius: 5px;
                margin: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <img src="/static/icon.png" alt="Logo" class="logo">
            <h1>Willkommen zu PP-CGA!</h1>
            <a href="de.pp.cga://instajoin?code={code}" class="join-button">Spiel beitreten</a>
            <div class="download-buttons">
                <a href="https://play.google.com/store/apps/details?id=de.pp.cga" target="_blank">Aus dem Playstore herunterladen</a>
                <a href="https://github.com/phillipc0/PP-CGA-FE/releases" target="_blank">APK herunterladen</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)
