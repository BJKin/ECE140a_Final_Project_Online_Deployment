import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException, status, Form, Body, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import uuid
import datetime
from typing import Dict, Optional
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
import mysql.connector as mysql
import os
from dotenv import load_dotenv
import httpx

# Import database functions
from app.database import (
    setup_database,
    get_user_by_email,
    get_user_by_id,
    create_user,
    create_session,
    get_session,
    delete_session,
    add_device,
    remove_device,
    get_devices,
    get_device,
    add_sensorData,
    get_device_by_mac_address,
    get_sensorData,
    add_clothing,
    get_clothing,
    remove_clothing,
    update_clothing,
    get_wardrobe
)

# Load enviromental variables
load_dotenv()

db_host = os.getenv('MYSQL_HOST')
db_user = os.getenv('MYSQL_USER')
db_pass = os.getenv('MYSQL_PASSWORD')
db_name = os.getenv('MYSQL_DATABASE')

# Set up FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for managing application startup and shutdown.
    Handles database setup and cleanup in a more structured way.
    """

    try:
        await setup_database() 
        print("Database setup completed")
        yield
    finally:
        print("Shutdown completed")


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# Static file helper
def read_html(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()


# Error page helper
def get_error_html(username: str) -> str:
    error_html = read_html("app/static/templates/error.html")
    return error_html.replace("{username}", username)


# Authentication
async def verify_session(request: Request):
    """Check if session is valid and return user data if it is"""
    
    sessionId = request.cookies.get("sessionId")
    if not sessionId:
        return None
    
    session = await get_session(sessionId)
    if not session:
        return None
    
    session_exp = session["expires_at"]
    time_now = datetime.datetime.now()
    if time_now >= session_exp:
        return None

    user = await get_user_by_id(session["user_id"])
    return user


#Home GET route
@app.get("/", response_class=HTMLResponse)
def get_index() -> HTMLResponse:
   """Return the index HTML page"""
   with open("app/static/templates/index.html") as html:
       return HTMLResponse(content=html.read())


#Dashboard GET route
@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request) -> HTMLResponse:
    """Return the dashboard HTML page if authenticated, redirect to login if not"""
    
    user = await verify_session(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    with open("app/static/templates/dashboard.html") as html:
        return HTMLResponse(content=html.read())


#Profile routes
@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Show signup if not signed up, or redirect to profile page"""

    user = await verify_session(request)

    if not user:
       return RedirectResponse(url="/login", status_code=303)
    return HTMLResponse(content=read_html("app/static/templates/profile.html"))

@app.get("/api/profile", response_class=JSONResponse)
async def get_user_profile(request: Request) -> JSONResponse:
    """Get profile information for the authenticated user"""

    user = await verify_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        user_info = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "location": user["location"],
            "created_at": user["created_at"].strftime('%Y-%m-%d %H:%M:%S')
        }
        return JSONResponse(user_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user info: {str(e)}")


#Signup routes
@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Show signup if not signed up, or redirect to profile page"""

    user = await verify_session(request)
    if user:
        return RedirectResponse(url=f"/profile", status_code=303)
    return HTMLResponse(content=read_html("app/static/templates/signup.html"))

@app.post("/signup")
async def signup(request: Request):
    """Create a new user and log them in"""
    
    form_data = await request.form()
    name = form_data.get("name")
    email = form_data.get("email")
    password = form_data.get("password")
    location = form_data.get("location", "")
    
    if not name or not email or not password:
        return HTMLResponse(content=read_html("app/static/templates/signup.html"))
    
    try:
        await create_user(name, email, password, location)
        user = await get_user_by_email(email)
        sessionId = str(uuid.uuid4())
        expires_at = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        await create_session(user["id"], sessionId, expires_at)
        
        response = RedirectResponse(url=f"/profile", status_code=303)
        response.set_cookie(key="sessionId", value=sessionId, httponly=True)
        return response
    
    except Exception as e:
        error_html = get_error_html(str(e))
        return HTMLResponse(content=error_html, status_code=500)


#Login/logout routes
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login if not logged in, or redirect to profile page"""

    user = await verify_session(request)
    if user:
        return RedirectResponse(url=f"/profile/", status_code=303)
    return HTMLResponse(content=read_html("app/static/templates/login.html"))

@app.post("/login")
async def login(request: Request):
    """Validate credentials and create a new session if valid"""
    
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")

    if not username or not password:
        return HTMLResponse(content=read_html("app/static/templates/login.html"))

    user = await get_user_by_email(username)
    if not user or user["password"] != password:
         error_html = get_error_html(username)
         return HTMLResponse(content=error_html, status_code=403)
    
    sessionId = str(uuid.uuid4())
    expires_at = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    await create_session(user["id"], sessionId, expires_at)
 
    response = RedirectResponse(url=f"/profile", status_code=303)
    response.set_cookie(key="sessionId", value=sessionId, httponly=True)
    return response

@app.post("/logout")
async def logout(request: Request):
    """Clear session and redirect to login page"""

    sessionId = request.cookies.get("sessionId")
    if sessionId:
        await delete_session(sessionId)

    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="sessionId")
    return response


# Device Management Routes
@app.get("/api/devices", response_class=JSONResponse)
async def get_user_devices(request: Request) -> JSONResponse:
    """Get all devices for the authenticated user"""

    user = await verify_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        devices = await get_devices(user["id"])
        return JSONResponse(devices)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get devices: {str(e)}")
    
@app.get("/api/devices/{device_id}", response_class=JSONResponse)
async def get_user_device(request: Request, device_id: str) -> JSONResponse:
    """Get a device for the authenticated user"""

    user = await verify_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        await get_device(user["id"], device_id)
        return JSONResponse({"success": True, "message": "A device was retrieved"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove device: {str(e)}")
    
@app.post("/api/devices", response_class=JSONResponse)
async def add_new_device(request: Request, device_id: str = Body(...), mac_address: str = Body(...)) -> JSONResponse:
    """Add a new device for the authenticated user"""

    user = await verify_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        await add_device(user["id"], device_id, mac_address)
        return JSONResponse({"success": True, "message": "Device added successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add device: {str(e)}")
    
@app.delete("/api/devices/{device_id}", response_class=JSONResponse)
async def remove_user_device(request: Request, device_id: str, mac_address: str = Query(...)) -> JSONResponse:
    """Remove a device for the authenticated user"""

    user = await verify_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        await remove_device(user["id"], device_id, mac_address)
        return JSONResponse({"success": True, "message": "Device removed successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove device: {str(e)}")

    

# Sensor Data Routes
@app.get("/api/devices/{device_id}/data", response_class=JSONResponse)
async def get_sensor_data(request: Request, device_id: int, start_date: str = Query(None), end_date: str = Query(None)) -> JSONResponse:
    """Get sensor data for a specific device"""

    user = await verify_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if not start_date:
        start_date = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    if not end_date:
        end_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        data = await get_sensorData(user["id"], device_id, start_date, end_date)
        
        formatted_data = []
        for record in data:
            formatted_data.append({
                "timestamp": record[0].strftime('%Y-%m-%d %H:%M:%S') if hasattr(record[0], 'strftime') else record[0],
                "temperature": record[1],
                "pressure": record[2],
                "temperature_unit": record[3],
                "pressure_unit": record[4]
            })
        
        return JSONResponse(formatted_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sensor data: {str(e)}")

@app.post("/api/devices/{device_id}/data", response_class=JSONResponse)
async def post_sensor_data(request: Request, device_id: int, temperature: float = Body(...), pressure: float = Body(...), temperature_unit: str = Body("°C"), pressure_unit: str = Body("hPa"), timestamp: str = Body(...)) -> JSONResponse:
    """Store sensor data for a device"""

    user = await verify_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        await add_sensorData(user["id"], device_id, temperature, pressure, temperature_unit, pressure_unit, timestamp)
        return JSONResponse({"success": True, "message": "Data added successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add sensor data: {str(e)}")

@app.post("/api/sensor-data/{mac_address}", response_class=JSONResponse)
async def receive_sensor_data(mac_address: str, temperature: float = Body(...), pressure: float = Body(...), temperature_unit: str = Body("°C"), pressure_unit: str = Body("hPa"), timestamp: str = Body(None)):
    """Receive sensor data from MQTT client"""
    
    try:
        device = await get_device_by_mac_address(mac_address)
        if not device:
            return JSONResponse(status_code=404, content={"error": f"No device found with MAC address: {mac_address}"})
        
        user_id = device["user_id"]
        device_id = device["id"]
        await add_sensorData(user_id, device_id, temperature, pressure, temperature_unit, pressure_unit, timestamp)
        return JSONResponse(status_code=200, content={"message": "Data received successfully"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to process sensor data: {str(e)}"})


# Wardrobe Management Routes
@app.get("/wardrobe", response_class=HTMLResponse)
async def wardrobe_page(request: Request):
    """Show wardrobe page if authenticated, redirect to login if not"""
    
    user = await verify_session(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return HTMLResponse(content=read_html("app/static/templates/wardrobe.html"))

@app.get("/api/wardrobe", response_class=JSONResponse)
async def get_user_wardrobe(request: Request) -> JSONResponse:
    """Get all clothing items for the authenticated user"""
    
    user = await verify_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        wardrobe = await get_wardrobe(user["id"])
        return JSONResponse(wardrobe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get wardrobe: {str(e)}")

@app.get("/api/wardrobe/{clothing_id}", response_class=JSONResponse)
async def get_user_wardrobe(request: Request, clothing_id: int) -> JSONResponse:
    """Get all clothing items for the authenticated user"""
    
    user = await verify_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        wardrobe = await get_clothing(user["id"], clothing_id)
        return JSONResponse(wardrobe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get clothing: {str(e)}")
    
@app.post("/api/wardrobe", response_class=JSONResponse)
async def add_clothing_item(request: Request, name: str = Body(...), color: str = Body(...)) -> JSONResponse:
    """Add a new clothing item to the wardrobe"""
    
    user = await verify_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        await add_clothing(user["id"], name, color)
        return JSONResponse({"success": True, "message": "Clothing item added successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add clothing item: {str(e)}")
    
@app.put("/api/wardrobe/{clothing_id}", response_class=JSONResponse)
async def update_clothing_item(request: Request, clothing_id: int, new_name: str = Body(...), new_color: str = Body(...)) -> JSONResponse:
    """Update a clothing item in the wardrobe"""
    
    user = await verify_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        await update_clothing(user["id"], clothing_id, new_name, new_color)
        return JSONResponse({"success": True, "message": "Clothing item updated successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update clothing item: {str(e)}")
    
@app.delete("/api/wardrobe/{clothing_id}", response_class=JSONResponse)
async def remove_clothing_item(request: Request, clothing_id: int) -> JSONResponse:
    """Remove a clothing item from the wardrobe"""
    
    user = await verify_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        await remove_clothing(user["id"], clothing_id)
        return JSONResponse({"success": True, "message": "Clothing item removed successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove clothing item: {str(e)}")


# AI api route
@app.post("/api/ai")
async def proxy_ai_complete(request: Request):
    try:
        data = await request.json()
        headers = {
            'Content-Type': 'application/json',
            'email': os.getenv('UCSD_EMAIL'),
            'pid': os.getenv('UCSD_PID')
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://ece140-wi25-api.frosty-sky-f43d.workers.dev/api/v1/ai/complete",
                json=data,
                headers=headers,
                timeout=30.0
            )
            return Response(content=response.content, status_code=response.status_code)
        
    except Exception as e:
        return JSONResponse(status_code=500,  content={"error": f"An unexpected error occurred: {str(e)}"})



if __name__ == "__main__":
   uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)