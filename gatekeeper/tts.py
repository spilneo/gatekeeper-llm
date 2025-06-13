# gatekeeper/tts.py
import subprocess
import speech_recognition as sr
from typing import Optional
from rich.console import Console

console = Console()

def say(text: str):
    """Uses the macOS 'say' command to speak the given text."""
    try:
        subprocess.run(["say", text], check=True, capture_output=True, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[yellow]Warning: 'say' command failed. Voice output is unavailable. (macOS only)[/yellow]")

def listen() -> Optional[str]:
    """Listens for audio via the microphone and transcribes it to text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        console.print("[cyan]Calibrating for ambient noise...[/cyan]")
        r.adjust_for_ambient_noise(source, duration=1)
        console.print("[bold green]Listening...[/bold green]")
        say("I'm listening")
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            console.print("[yellow]No speech detected.[/yellow]")
            say("I didn't hear anything.")
            return None

    try:
        console.print("[cyan]Recognizing speech...[/cyan]")
        # Using Google's speech recognition for a simple, dependency-light experience.
        text = r.recognize_google(audio)
        console.print(f"[dim]Recognized:[/dim] '{text}'")
        return text
    except sr.RequestError as e:
        console.print(f"[red]API request failed; {e}[/red]")
        say("Sorry, I couldn't reach the speech recognition service.")
    except sr.UnknownValueError:
        console.print("[red]Could not understand audio.[/red]")
        say("I'm sorry, I couldn't understand what you said.")
    return None