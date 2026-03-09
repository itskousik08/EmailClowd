import os
import smtplib
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from rich.console import Console
from rich.prompt import Prompt
from art import text2art
import ollama

app = Flask(__name__)
app.config['SECRET_KEY'] = 'emailclowd_secret'
socketio = SocketIO(app, cors_allowed_origins="*")
console = Console()

# Global variables store karne ke liye
USER_CONFIG = {
    "model": "",
    "email": "",
    "app_password": ""
}

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def setup_cli():
    clear_terminal()
    
    # 1. Colorful Banner
    banner = text2art("EmailClowd", font='slant')
    console.print(f"[bold magenta]{banner}[/bold magenta]")
    console.print("[bold cyan]Welcome to EmailClowd - Your Local AI Email Assistant[/bold cyan]\n")
    
    # 2. Fetch Ollama Models
    try:
        models_info = ollama.list()
        models = [m['model'] for m in models_info['models']]
    except Exception as e:
        console.print("[bold red]❌ Error: Ollama is not running. Please start Ollama first.[/bold red]")
        exit(1)

    if not models:
        console.print("[bold red]❌ No models found in Ollama. Pull a model using 'ollama run llama3'.[/bold red]")
        exit(1)

    console.print("[bold green]🤖 Installed Ollama Models:[/bold green]")
    for i, model in enumerate(models):
        console.print(f"  [[bold yellow]{i+1}[/bold yellow]] {model}")
    
    model_choice = int(Prompt.ask("\nSelect the Model Number you want to use", choices=[str(i+1) for i in range(len(models))]))
    USER_CONFIG["model"] = models[model_choice - 1]
    console.print(f"[bold green]✔ Connected to {USER_CONFIG['model']}[/bold green]\n")

    # 3. Ask for Email Credentials
    console.print("[bold magenta]--- Email Setup ---[/bold magenta]")
    USER_CONFIG["email"] = Prompt.ask("[bold yellow]Enter your Email Address[/bold yellow]")
    USER_CONFIG["app_password"] = Prompt.ask("[bold yellow]Enter your App Password[/bold yellow]", password=True)
    
    console.print("\n[bold green]✅ Setup Complete! Starting Local Server...[/bold green]")
    console.print("[bold cyan]🌐 Open http://127.0.0.1:5000 in your browser[/bold cyan]\n")

# --- WEB & AI LOGIC ---

@app.route('/')
def index():
    return render_template('index.html', model=USER_CONFIG["model"], email=USER_CONFIG["email"])

@socketio.on('send_task')
def handle_task(data):
    user_task = data['task']
    # UI me update bhejna
    emit('ai_reply', {'sender': 'ai', 'text': f'⏳ Working on it... (Using {USER_CONFIG["model"]})'})
    
    # AI Logic (Ollama se connect karna)
    try:
        system_prompt = "You are EmailClowd, an AI email assistant. Help the user draft emails, summarize emails, or write professional replies."
        
        # Here you can add logic to detect if the user wants to "SEND EMAIL" or "SUMMARIZE" 
        # For now, it chats and drafts emails based on user prompt.
        
        response = ollama.chat(model=USER_CONFIG["model"], messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_task}
        ])
        
        ai_response = response['message']['content']
        emit('ai_reply', {'sender': 'ai', 'text': ai_response})
        
    except Exception as e:
        emit('ai_reply', {'sender': 'ai', 'text': f'❌ Error: {str(e)}'})

if __name__ == '__main__':
    setup_cli()
    # Start server
    socketio.run(app, host='127.0.0.1', port=5000, debug=False, allow_unsafe_werkzeug=True)
