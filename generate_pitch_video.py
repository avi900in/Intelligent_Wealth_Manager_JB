"""
Bank Julius Baer & Co. Ltd. — Wealth Intelligence Demo Video Generator
Combines high-resolution browser UI walkthrough frames with a professional voiceover into a standalone MP4 video.
"""

import os
import subprocess
import shutil
from PIL import Image, ImageSequence

try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG_EXE = "ffmpeg"

SCRIPT_TEXT = """Welcome to JB Pulse, the AI-powered Wealth Intelligence Cockpit engineered for Bank Julius Baer.

Private wealth management is undergoing a paradigm shift. Today, Relationship Managers oversee complex multi-asset portfolios across multiple jurisdictions, navigating real-time market shocks, portfolio drift, credit facility covenants, and qualitative client instructions.

JB Pulse transforms this complexity into proactive, institutional-grade intelligence.

On the Executive Cockpit, Priscilla Ong immediately accesses her entire five hundred and ninety-six million dollar Asia book: twenty active HNW clients, real-time AUM return metrics, eighty-seven mandate breaches, and live market shock transmissions — backed by Row-Level Security and Zero-PII presentation privacy.

Every morning, rather than sifting through endless spreadsheets, the RM opens the Prioritized Morning Call Queue.

Our deterministic orchestration engine dynamically ranks all twenty clients by an explainable composite urgency score, factoring in Lombard credit facility headroom, private equity capital calls, and asset allocation drift.

At the top of the queue is Hartono Wijaya Kusuma with an 85 urgency score, followed by Cheung Kwok Wing. Each card provides instant risk badges and a one-sentence priority action.

Drilling down into the Client 360 Dossier for Hartono Kusuma, we see complete multi-portfolio look-through exposure across Active Growth and Income sleeves. The deterministic analytics layer mathematically checks every holding against Strategic Asset Allocation bands — surfacing exact overweight breaches.

Crucially, JB Pulse extracts qualitative RM meeting notes as hard constraints. When Hartono states that his family will never sell their legacy energy shares in Bara Nusantara, our system recognizes this not as an anomaly, but as a binding governance rule.

The Intelligent Agent Action Deck is our core engine. Here, our specialist agent swarm — Rebalancing, Tax Optimization, Liquidity, Market Impact, and RM Notes — collaborates under the Master Orchestrator.

Notice our breakthrough feature: The Synergistic Comingling Opportunity. Instead of bombarding the client with disconnected trades, the Orchestrator synthesizes a Multi-Objective Strategy. It clubs liquid de-risking in global equities, harvests available tax losses, ring-fences cash for upcoming milestones, and reconciles the standing Bara Nusantara conflict under an explicit suitability waiver.

When the RM clicks Approve Action, our Morning Call Urgency Simulator instantly updates, quantifying a forty-point drop in portfolio risk.

Beyond daily rebalancing, RMs have dedicated institutional tools in the Navigation Menu.

The Portfolio Stress Testing Lab simulates instantaneous macroeconomic shocks — from Middle East geopolitical escalations and Treasury yield shifts to Yen carry trade unwinds. The simulator decomposes risk factor attribution and outputs an AI Proactive Hedging Blueprint.

The Trigger-to-Conversation Engine converts macro events into bespoke client-ready WhatsApp drafts, phone call scripts with objection handling, and formal executive emails tailored directly to each client's behavioral persona and holdings.

Finally, the Client Meeting Pack and Governance Dossier.

Private banking demands uncompromising compliance. When Supervisory Desk Head Marc Guggenheim logs in, the system enforces a read-only audit mode. He reviews the 4-Point Supervisory Governance Audit — validating KYC status, mandate suitability, and standing exclusions.

With one click, he executes the Supervisory Endorsement Stamp, generating an immutable, audit-certified meeting pack ready for client delivery.

JB Pulse: Turning Wealth Intelligence into Client Alpha. Thank you."""

def generate_video(
    input_recording_path: str = "jb_pulse_judges_demo_walkthrough_1788676933453.webp",
    output_mp4_path: str = "Julius_Baer_Wealth_Intelligence_Demo.mp4"
):
    print("1. Synthesizing voiceover audio track via macOS speech engine...")
    audio_aiff = "temp_voiceover.aiff"
    audio_m4a = "temp_voiceover.m4a"
    
    subprocess.run(["say", "-v", "Daniel", "-r", "180", "-o", audio_aiff, SCRIPT_TEXT], check=True)
    subprocess.run(["afconvert", "-f", "mp4f", "-d", "aac", audio_aiff, audio_m4a], check=True)
    
    # Check audio duration
    probe = subprocess.run([FFMPEG_EXE, "-i", audio_m4a], stderr=subprocess.PIPE, text=True)
    duration_sec = 223.48
    for line in probe.stderr.splitlines():
        if "Duration" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            duration_sec = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
            break
            
    print(f"   Audio duration: {duration_sec:.2f} seconds")

    print(f"2. Loading video frames from {input_recording_path}...")
    im = Image.open(input_recording_path)
    frames = [f.copy().convert("RGB") for f in ImageSequence.Iterator(im)]
    total_frames = len(frames)
    fps = total_frames / duration_sec
    print(f"   Extracted {total_frames} frames ({frames[0].width}x{frames[0].height}), encoding at {fps:.3f} FPS...")

    print(f"3. Encoding MP4 with H.264 video & AAC audio...")
    cmd = [
        FFMPEG_EXE,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{frames[0].width}x{frames[0].height}",
        "-pix_fmt", "rgb24",
        "-r", f"{fps}",
        "-i", "-",
        "-i", audio_m4a,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_mp4_path
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for frame in frames:
        proc.stdin.write(frame.tobytes())
    stdout, stderr = proc.communicate()

    # Cleanup temp audio
    for f in [audio_aiff, audio_m4a]:
        if os.path.exists(f):
            os.remove(f)

    if proc.returncode == 0:
        print(f"Done! Video generated: {output_mp4_path} ({os.path.getsize(output_mp4_path)/1e6:.2f} MB)")
    else:
        print("Error during encoding:", stderr.decode("utf-8", errors="ignore"))

if __name__ == "__main__":
    generate_video()
