#!/usr/bin/env python3
"""
RIG LinkedIn Studio — CrewAI Agent Orchestration

Agents:
  - ContentStrategist: Plans content calendar, scores post ideas
  - ImageDirector: Runs Higgsfield pipeline, validates SHIP/PASS
  - PublisherAgent: Postiz integration, scheduling, cross-platform
  - ProspectingAgent: ICP scoring, company discovery, outreach
  - GoldenHourAgent: Engagement protocol, comments, DMs, views
  - AnalyticsAgent: KPI tracking, daily reports, growth metrics

Orchestrated by Archon workflows with Langfuse tracing.
"""
import os
import subprocess
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

CREWAI_AVAILABLE = False
try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── Agent Definitions ──

CONTENT_STRATEGIST_CONFIG = {
    "role": "LinkedIn Content Strategist",
    "goal": "Plan and execute a 20-day AI thought leadership campaign with maximum engagement",
    "backstory": """You are a LinkedIn content strategist specializing in B2B healthcare AI.
    You understand the ICP (medspa, law, dental, manufacturing, PE) and craft hooks
    that resonate with buyers and hiring managers alike. Your posts combine cultural
    references with technical credibility to create scroll-stopping content.""",
    "tools": ["read_file", "web_search", "bash"],
}

IMAGE_DIRECTOR_CONFIG = {
    "role": "AI Image Director (Higgsfield Operator)",
    "goal": "Generate cinematic, brand-consistent images for every LinkedIn post",
    "backstory": """You operate the Higgsfield image generation pipeline with Soul ID
    muscular-man (a4c09954). You know the cinematic_studio_2_5 model inside out.
    Every image must pass the 3-check Verifier: scene fidelity 85+, text legibility 90+,
    brand fidelity 80+. SHIP or it doesn't go out.""",
    "tools": ["bash", "read_file"],
}

PUBLISHER_CONFIG = {
    "role": "Postiz Publisher Agent",
    "goal": "Schedule and publish all LinkedIn posts through Postiz with images",
    "backstory": """You manage the Postiz CLI for cross-platform publishing.
    You upload images, create posts, schedule across LinkedIn personal, LinkedIn company,
    and other channels. You verify post IDs, confirm schedules, and log all publishes.""",
    "tools": ["bash"],
}

PROSPECTING_CONFIG = {
    "role": "RIG Prospecting Agent",
    "goal": "Find and score ICP-matching prospects for RIG GTM Studio",
    "backstory": """You run the prospect scoring pipeline against ICP v2.1.
    You score companies across 4 dimensions: firmographic fit, pain signals,
    decision authority, and timing urgency. You prioritize A1 (80+) prospects
    for immediate outreach and maintain the prospect pipeline.""",
    "tools": ["bash", "web_search", "read_file"],
}

GOLDEN_HOUR_CONFIG = {
    "role": "Golden Hour Engagement Agent",
    "goal": "Execute 9-step engagement protocol within 90 minutes of post publish",
    "backstory": """You execute the golden hour protocol to maximize algorithmic signal.
    Comments, DMs, profile views, follows — timed precisely to trigger LinkedIn's
    engagement flywheel. You log every action for accountability and KPI tracking.""",
    "tools": ["bash", "web_search"],
}

ANALYTICS_CONFIG = {
    "role": "LinkedIn Analytics Agent",
    "goal": "Track KPIs and generate daily performance reports",
    "backstory": """You monitor all 3 work tracks: Personal Brand, Get Mike Hired,
    RIG Business. You check daily goals against published content, engagement
    metrics, and prospect pipeline health. You produce morning and evening reports.""",
    "tools": ["bash", "read_file"],
}


def create_agent(config: dict, verbose: bool = True) -> object:
    """Create a CrewAI agent from config dict."""
    if not CREWAI_AVAILABLE:
        print(f"⚠ CrewAI not installed — {config['role']} agent created as stub")
        return None
    
    return Agent(
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        verbose=verbose,
        allow_delegation=False,
        tools=config.get("tools", []),
    )


def create_crew(mode: str = "sequential") -> object:
    """Create a CrewAI crew for LinkedIn operations."""
    if not CREWAI_AVAILABLE:
        return None
    
    agents = {
        "content": create_agent(CONTENT_STRATEGIST_CONFIG),
        "image": create_agent(IMAGE_DIRECTOR_CONFIG),
        "publish": create_agent(PUBLISHER_CONFIG),
        "prospecting": create_agent(PROSPECTING_CONFIG),
        "golden_hour": create_agent(GOLDEN_HOUR_CONFIG),
        "analytics": create_agent(ANALYTICS_CONFIG),
    }
    
    # Daily publishing task
    publish_task = Task(
        description="Execute daily LinkedIn publishing pipeline for post 27 Beyoncé ProofPacket theme",
        expected_output="Published LinkedIn post with SHIP-verified image and Postiz confirmation",
        agent=agents["publish"],
    )
    
    # Golden hour task
    golden_task = Task(
        description="Execute golden hour engagement for the most recently published post",
        expected_output="Completed golden hour log with 9 steps executed",
        agent=agents["golden_hour"],
    )
    
    # Prospecting task
    prospect_task = Task(
        description="Run prospecting scraper and score new prospects against ICP v2.1",
        expected_output="25+ scored prospects with A1/A2 priority buckets saved to JSON",
        agent=agents["prospecting"],
    )
    
    tasks = [publish_task, golden_task, prospect_task]
    
    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential if mode == "sequential" else Process.hierarchical,
        verbose=True,
    )
    
    return crew


def run_daily_pipeline():
    """Run the full daily LinkedIn pipeline via CrewAI."""
    if not CREWAI_AVAILABLE:
        print("⚠ CrewAI not installed. Run: pip install crewai")
        return None
    
    crew = create_crew(mode="sequential")
    result = crew.kickoff()
    return result


def run_step(step_name: str, *args, **kwargs):
    """Run a single pipeline step with Langfuse tracing."""
    from langfuse_trace import trace_pipeline
    
    with trace_pipeline(step_name) as trace:
        span = trace.step(step_name, {"args": str(args)})
        
        if step_name == "publish":
            # Run the rig-viral pipeline
            result = subprocess.run(
                [str(PROJECT_ROOT / "bin" / "rig-viral"), "run", *args],
                capture_output=True, text=True, timeout=300
            )
            output = {"status": "complete" if result.returncode == 0 else "failed"}
        
        elif step_name == "golden_hour":
            # Run golden hour script
            result = subprocess.run(
                ["python3", str(PROJECT_ROOT / "scripts" / "golden_hour.py"), *args],
                capture_output=True, text=True, timeout=5400
            )
            output = {"status": "complete" if result.returncode == 0 else "failed"}
        
        elif step_name == "prospect":
            # Run prospect scraper
            result = subprocess.run(
                ["python3", str(PROJECT_ROOT / "scripts" / "prospect_scraper.py"), "--all"],
                capture_output=True, text=True, timeout=120
            )
            output = {"status": "complete" if result.returncode == 0 else "failed"}
        
        else:
            output = {"status": "unknown_step"}
        
        trace.end_step(span, output, ok=output.get("status") == "complete")
        return output


# ── CLI ──
def main():
    import argparse
    parser = argparse.ArgumentParser(description="CrewAI orchestration for RIG LinkedIn Studio")
    parser.add_argument("--run", choices=["all", "publish", "golden-hour", "prospect"], 
                       help="Run pipeline step")
    parser.add_argument("--status", action="store_true", help="Show agent status")
    args = parser.parse_args()
    
    if args.status:
        print(f"CrewAI: {'✅ Available' if CREWAI_AVAILABLE else '⚠ NOT installed (pip install crewai)'}")
        for name in ["ContentStrategist", "ImageDirector", "PublisherAgent", 
                     "ProspectingAgent", "GoldenHourAgent", "AnalyticsAgent"]:
            print(f"  {name}: {'✅ Ready' if CREWAI_AVAILABLE else '⚠ Stub'}")
    
    if args.run:
        run_step(args.run.replace("-", "_"))


if __name__ == "__main__":
    main()
