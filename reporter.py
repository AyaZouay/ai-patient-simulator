# reporter.py
# Saves call transcripts and recordings in an organized way

import os
import json
from datetime import datetime

def save_transcript(scenario_id, scenario_name, conversation_log, output_dir="transcripts"):
    """
    Saves the full conversation transcript to a text file.
    
    scenario_id: which scenario this was (1-10)
    scenario_name: human readable name
    conversation_log: list of exchanges [{speaker, text}]
    """
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"transcript_{scenario_id:02d}_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    
    # Make sure directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Write the transcript
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"CALL TRANSCRIPT\n")
        f.write(f"{'='*50}\n")
        f.write(f"Scenario: {scenario_name}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*50}\n\n")
        
        for exchange in conversation_log:
            speaker = exchange["speaker"]
            text = exchange["text"]
            f.write(f"{speaker}: {text}\n\n")
    
    print(f"Transcript saved: {filepath}")
    return filepath


def save_bug_report(bugs, output_dir="reports"):
    """
    Saves the bug report as a markdown file.
    
    bugs: list of bug dictionaries
    """
    
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "bug_report.md")
    
    with open(filepath, "w") as f:
        f.write("# Bug Report — Pretty Good AI Agent Testing\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Total issues found: {len(bugs)}\n\n")
        f.write("---\n\n")
        
        for i, bug in enumerate(bugs, 1):
            f.write(f"## Bug #{i}: {bug['title']}\n\n")
            f.write(f"**Severity:** {bug['severity']}\n\n")
            f.write(f"**Scenario:** {bug['scenario']}\n\n")
            f.write(f"**Transcript:** {bug['transcript_file']}\n\n")
            f.write(f"**Timestamp in call:** {bug['timestamp']}\n\n")
            f.write(f"**What happened:** {bug['what_happened']}\n\n")
            f.write(f"**Why it's a problem:** {bug['why_problem']}\n\n")
            f.write(f"**Expected behavior:** {bug['expected']}\n\n")
            f.write("---\n\n")
    
    print(f"Bug report saved: {filepath}")
    return filepath

def merge_call_recordings(scenario_id, recordings_dir="recordings"):
    """
    Merges all turn files from a call into one complete MP3.
    Alternates between patient and agent turns in order.
    """
    from pydub import AudioSegment
    import glob
    
    # Get all turn files for this call, sorted by turn number
    turn_files = sorted(
        glob.glob(os.path.join(recordings_dir, "turn_*.mp3")),
        key=lambda x: (
            int(x.split("turn_")[1].split("_")[0]),  # sort by turn number
             0 if "patient" in x and "turn_0" in x else (1 if "agent" in x else 2)
        )
    )
        
    # Filter out the complete file if it exists
    turn_files = [f for f in turn_files if "complete" not in f]
    
    # print("Merging in this order:")
    # for f in turn_files:
    #     print(f"  {f}")
    if not turn_files:
        print("No turn files found to merge")
        return None
    
    # Merge all turns into one audio file
    combined = AudioSegment.empty()
    silence = AudioSegment.silent(duration=500)  # 0.5 second pause between turns
    
    for turn_file in turn_files:
        if os.path.exists(turn_file):
            audio = AudioSegment.from_mp3(turn_file)
            combined += audio + silence
    
    # Save merged file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(recordings_dir, f"call_{scenario_id:02d}_complete_{timestamp}.mp3")
    combined.export(output_path, format="mp3")
    
    # Delete individual turn files to keep things clean
    for turn_file in turn_files:
        os.remove(turn_file)
    
    print(f"Complete recording saved: {output_path}")
    return output_path