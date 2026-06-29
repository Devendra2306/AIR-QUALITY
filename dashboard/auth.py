import os
from functools import wraps
from dash import dcc, html
from dash.dependencies import Input, Output, State


# Simple authentication configuration
# In production, use proper auth like OAuth2, JWT, or session-based auth
AUTH_USERNAME = os.environ.get("DASH_USERNAME", "admin")
AUTH_PASSWORD = os.environ.get("DASH_PASSWORD", "admin123")


def is_authenticated(session_id):
    """Check if session is authenticated."""
    # In production, use proper session management
    # For now, we'll use a simple in-memory approach
    return False


def login_layout():
    """Return login page layout."""
    return html.Div([
        html.Div([
            html.H2("Air Quality Dashboard", style={"textAlign": "center", "marginBottom": "30px"}),
            html.Div([
                html.Label("Username", style={"display": "block", "marginBottom": "5px"}),
                dcc.Input(
                    id="login-username",
                    type="text",
                    placeholder="Enter username",
                    style={"width": "100%", "padding": "10px", "marginBottom": "15px"}
                ),
                html.Label("Password", style={"display": "block", "marginBottom": "5px"}),
                dcc.Input(
                    id="login-password",
                    type="password",
                    placeholder="Enter password",
                    style={"width": "100%", "padding": "10px", "marginBottom": "15px"}
                ),
                html.Button(
                    "Login",
                    id="login-button",
                    n_clicks=0,
                    style={
                        "width": "100%",
                        "padding": "12px",
                        "backgroundColor": "#2563eb",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "8px",
                        "cursor": "pointer",
                        "fontSize": "16px"
                    }
                ),
                html.Div(id="login-error", style={"color": "red", "marginTop": "15px", "textAlign": "center"})
            ], style={
                "maxWidth": "400px",
                "margin": "0 auto",
                "padding": "30px",
                "backgroundColor": "white",
                "borderRadius": "8px",
                "boxShadow": "0 4px 6px rgba(0,0,0,0.1)"
            })
        ], style={
            "minHeight": "100vh",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "backgroundColor": "#f4f7fb"
        })
    ])


def require_auth(callback):
    """Decorator to require authentication for callbacks."""
    @wraps(callback)
    def wrapper(*args, **kwargs):
        # In production, check session authentication
        # For now, we'll skip this for simplicity
        return callback(*args, **kwargs)
    return wrapper
