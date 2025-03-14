#!/usr/bin/env python3
"""
VOTai Ecosystem Analyzer

This module provides a comprehensive analysis tool for the VOTai Agent Ecosystem.
It can analyze the architecture, performance, and generate recommendations.

Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add the parent directory to sys.path to import local_mcp
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import the VOTai ASCII art
from src.vot1.local_mcp.ascii_art import get_votai_ascii

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ecosystem_analysis_report.log')
    ]
)
logger = logging.getLogger(__name__)

class EcosystemAnalyzer:
    """
    Analyzes the VOTai Agent Ecosystem and generates comprehensive reports.
    
    Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
    """
    
    def __init__(self, host="localhost", port=5678, output_file="ecosystem_analysis_report.md"):
        """
        Initialize the Ecosystem Analyzer.
        
        Args:
            host: Host address of the agent ecosystem server
            port: Port of the agent ecosystem server
            output_file: Path to save the analysis report
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.output_file = output_file
        self.dev_agent_id = None
        self.all_agents = []
        self.system_metrics = {}
        self.analysis_results = {}
        
        # Display VOTai signature
        votai_ascii = get_votai_ascii("large")
        logger.info(f"\n{votai_ascii}\nVOTai Ecosystem Analyzer initialized")

    def verify_server(self) -> bool:
        """
        Verify the server is running and get basic status information.
        
        Returns:
            bool: True if the server is running, False otherwise
        """
        try:
            logger.info(f"Verifying server at {self.base_url}")
            response = requests.get(f"{self.base_url}/api/status")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Server status: {data.get('status')}")
                self.system_metrics["status"] = data
                return True
            else:
                logger.error(f"Server status check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error connecting to server: {e}")
            return False
    
    def get_all_agents(self) -> bool:
        """
        Get a list of all agents in the ecosystem.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Getting list of all agents...")
            response = requests.get(f"{self.base_url}/api/agents")
            
            if response.status_code == 200:
                data = response.json()
                self.all_agents = data.get("agents", [])
                logger.info(f"Found {len(self.all_agents)} agents")
                return True
            else:
                logger.error(f"Failed to get agents: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error getting agents: {e}")
            return False
    
    def create_development_agent(self) -> bool:
        """
        Create a specialized DevelopmentAgent for ecosystem analysis.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Creating specialized DevelopmentAgent for ecosystem analysis...")
            payload = {
                "name": "EcosystemAnalyzer",
                "agent_type": "DevelopmentAgent",
                "capabilities": [
                    "code_generation",
                    "code_review",
                    "repository_analysis",
                    "testing",
                    "debugging",
                    "ecosystem_analysis"
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/api/agents",
                json=payload
            )
            
            if response.status_code == 201:
                data = response.json()
                self.dev_agent_id = data.get("agent_id") or data.get("agent", {}).get("id")
                
                if self.dev_agent_id:
                    logger.info(f"Created DevelopmentAgent with ID: {self.dev_agent_id}")
                    return True
                else:
                    logger.error("Agent created but no ID returned")
                    return False
            else:
                logger.error(f"Failed to create agent: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            return False
    
    def analyze_agent_metrics(self) -> bool:
        """
        Collect metrics from all agents that support the get_metrics task.
        
        Returns:
            bool: True if at least one agent provided metrics, False otherwise
        """
        if not self.all_agents:
            logger.error("No agents found to analyze")
            return False
        
        success = False
        self.analysis_results["agent_metrics"] = {}
        
        for agent in self.all_agents:
            agent_id = agent.get("id")
            agent_name = agent.get("name")
            agent_type = agent.get("type", "Unknown")
            
            logger.info(f"Collecting metrics from agent {agent_name} ({agent_id})")
            
            try:
                # Only development agents support metrics for now
                if "DevelopmentAgent" not in agent_type:
                    logger.info(f"Agent {agent_name} ({agent_type}) does not support metrics")
                    continue
                
                payload = {
                    "task_type": "get_metrics",
                    "task_data": {}
                }
                
                response = requests.post(
                    f"{self.base_url}/api/agents/{agent_id}/task",
                    json=payload
                )
                
                if response.status_code != 201:
                    logger.warning(f"Failed to request metrics from agent {agent_name}: {response.status_code}")
                    continue
                
                task_id = response.json().get("task_id")
                logger.info(f"Added metrics task with ID: {task_id} for agent {agent_name}")
                
                # Wait for task completion
                metrics_data = self.wait_for_response_data(agent_id, task_id, max_wait=30)
                
                if not metrics_data:
                    logger.warning(f"No metrics data received from agent {agent_name}")
                    continue
                
                metrics = metrics_data.get("metrics", {})
                if metrics:
                    self.analysis_results["agent_metrics"][agent_id] = {
                        "name": agent_name,
                        "type": agent_type,
                        "metrics": metrics
                    }
                    success = True
                    
                    logger.info(f"Collected metrics from {agent_name}:")
                    logger.info(f"  Uptime: {metrics.get('uptime_formatted', 'N/A')}")
                    logger.info(f"  Tasks processed: {metrics.get('tasks_processed', 0)}")
                    logger.info(f"  Success rate: {metrics.get('success_rate', 0):.1f}%")
                
            except Exception as e:
                logger.error(f"Error collecting metrics from agent {agent_name}: {e}")
        
        return success
    
    def analyze_ecosystem_architecture(self) -> bool:
        """
        Analyze the ecosystem architecture using the DevelopmentAgent.
        
        This task requests a comprehensive analysis of the ecosystem architecture
        using Claude 3.7 in stream hybrid mode.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.dev_agent_id:
            logger.error("No DevelopmentAgent available for architecture analysis")
            return False
        
        try:
            logger.info("Requesting ecosystem architecture analysis...")
            
            # Prepare system information for analysis
            system_info = {
                "agents": [
                    {
                        "id": agent.get("id"),
                        "name": agent.get("name"),
                        "type": agent.get("type", "Unknown"),
                        "capabilities": agent.get("capabilities", [])
                    }
                    for agent in self.all_agents
                ],
                "metrics": self.analysis_results.get("agent_metrics", {}),
                "server_status": self.system_metrics.get("status", {})
            }
            
            payload = {
                "task_type": "analyze_ecosystem",
                "task_data": {
                    "system_info": system_info,
                    "analysis_depth": "comprehensive",
                    "focus_areas": [
                        "architecture",
                        "performance",
                        "integration",
                        "scalability",
                        "reliability"
                    ],
                    "ai_model": "claude-3-7-sonnet",
                    "mode": "stream_hybrid",
                    "max_tokens": 120000,
                    "thinking_tokens": 60000
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/agents/{self.dev_agent_id}/task",
                json=payload
            )
            
            if response.status_code != 201:
                logger.error(f"Failed to request architecture analysis: {response.status_code} - {response.text}")
                return False
            
            task_id = response.json().get("task_id")
            logger.info(f"Added architecture analysis task with ID: {task_id}")
            
            # Wait for task completion (longer timeout for comprehensive analysis)
            analysis_data = self.wait_for_response_data(self.dev_agent_id, task_id, max_wait=300)
            
            if not analysis_data:
                logger.error("Architecture analysis failed or timed out")
                return False
            
            # Extract architecture analysis
            architecture_analysis = analysis_data.get("analysis", "")
            if architecture_analysis:
                self.analysis_results["architecture"] = architecture_analysis
                logger.info("Successfully received architecture analysis")
                return True
            else:
                logger.error("Received empty architecture analysis")
                return False
                
        except Exception as e:
            logger.error(f"Error analyzing ecosystem architecture: {e}")
            return False
    
    def analyze_performance(self) -> bool:
        """
        Analyze the ecosystem performance using the DevelopmentAgent.
        
        This task requests a performance analysis of the ecosystem
        using Claude 3.7 in stream hybrid mode.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.dev_agent_id:
            logger.error("No DevelopmentAgent available for performance analysis")
            return False
        
        try:
            logger.info("Requesting ecosystem performance analysis...")
            
            # Use the metrics we've already collected
            performance_data = {
                "agent_metrics": self.analysis_results.get("agent_metrics", {}),
                "server_status": self.system_metrics.get("status", {})
            }
            
            payload = {
                "task_type": "analyze_performance",
                "task_data": {
                    "performance_data": performance_data,
                    "analysis_depth": "comprehensive",
                    "optimization_focus": [
                        "response_time",
                        "throughput",
                        "resource_usage",
                        "scalability"
                    ],
                    "ai_model": "claude-3-7-sonnet",
                    "mode": "stream_hybrid",
                    "max_tokens": 120000,
                    "thinking_tokens": 60000
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/agents/{self.dev_agent_id}/task",
                json=payload
            )
            
            if response.status_code != 201:
                logger.error(f"Failed to request performance analysis: {response.status_code} - {response.text}")
                return False
            
            task_id = response.json().get("task_id")
            logger.info(f"Added performance analysis task with ID: {task_id}")
            
            # Wait for task completion
            performance_data = self.wait_for_response_data(self.dev_agent_id, task_id, max_wait=300)
            
            if not performance_data:
                logger.error("Performance analysis failed or timed out")
                return False
            
            # Extract performance analysis
            performance_analysis = performance_data.get("analysis", "")
            if performance_analysis:
                self.analysis_results["performance"] = performance_analysis
                logger.info("Successfully received performance analysis")
                return True
            else:
                logger.error("Received empty performance analysis")
                return False
                
        except Exception as e:
            logger.error(f"Error analyzing ecosystem performance: {e}")
            return False
    
    def generate_recommendations(self) -> bool:
        """
        Generate improvement recommendations using the DevelopmentAgent.
        
        This task requests comprehensive recommendations for improving
        the ecosystem using Claude 3.7 in stream hybrid mode.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.dev_agent_id:
            logger.error("No DevelopmentAgent available for generating recommendations")
            return False
        
        try:
            logger.info("Requesting ecosystem improvement recommendations...")
            
            # Compile all analyses for generating recommendations
            analysis_data = {
                "architecture": self.analysis_results.get("architecture", ""),
                "performance": self.analysis_results.get("performance", ""),
                "agent_metrics": self.analysis_results.get("agent_metrics", {})
            }
            
            payload = {
                "task_type": "generate_recommendations",
                "task_data": {
                    "analysis_data": analysis_data,
                    "recommendation_areas": [
                        "architecture",
                        "performance",
                        "reliability",
                        "scalability",
                        "integration",
                        "security"
                    ],
                    "ai_model": "claude-3-7-sonnet",
                    "mode": "stream_hybrid",
                    "max_tokens": 120000,
                    "thinking_tokens": 60000
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/agents/{self.dev_agent_id}/task",
                json=payload
            )
            
            if response.status_code != 201:
                logger.error(f"Failed to request recommendations: {response.status_code} - {response.text}")
                return False
            
            task_id = response.json().get("task_id")
            logger.info(f"Added recommendations task with ID: {task_id}")
            
            # Wait for task completion
            recommendations_data = self.wait_for_response_data(self.dev_agent_id, task_id, max_wait=300)
            
            if not recommendations_data:
                logger.error("Recommendations generation failed or timed out")
                return False
            
            # Extract recommendations
            recommendations = recommendations_data.get("recommendations", "")
            if recommendations:
                self.analysis_results["recommendations"] = recommendations
                logger.info("Successfully received recommendations")
                return True
            else:
                logger.error("Received empty recommendations")
                return False
                
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return False
    
    def wait_for_response_data(self, agent_id: str, task_id: str, max_wait: int = 60) -> Optional[Dict[str, Any]]:
        """
        Wait for a response to a task and return the response data.
        
        Args:
            agent_id: ID of the agent
            task_id: ID of the task
            max_wait: Maximum time to wait in seconds
            
        Returns:
            Response data if found, None otherwise
        """
        logger.info(f"Waiting for response data for task {task_id}...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"{self.base_url}/api/agents/{agent_id}/response")
                
                if response.status_code == 200:
                    responses = response.json().get("responses", [])
                    
                    for resp in responses:
                        if resp.get("task_id") == task_id:
                            logger.info(f"Found response for task {task_id}")
                            return resp
                
                logger.info(f"No response yet, waiting... (elapsed: {time.time() - start_time:.1f}s)")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error checking for response: {e}")
                time.sleep(5)
        
        logger.error(f"Timed out waiting for response to task {task_id}")
        return None
    
    def generate_report(self) -> bool:
        """
        Generate a comprehensive ecosystem analysis report.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Generating comprehensive ecosystem analysis report...")
            
            # Get current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Create the report content
            report = [
                f"# VOTai Ecosystem Analysis Report",
                f"{get_votai_ascii('medium')}",
                f"Generated on: {timestamp}",
                "",
                "## System Overview",
                "",
                f"- **Host**: {self.host}",
                f"- **Port**: {self.port}",
                f"- **Agents**: {len(self.all_agents)}",
                "",
                "### Agents",
                ""
            ]
            
            # Add agent information
            for agent in self.all_agents:
                report.append(f"- **{agent['name']}** (ID: {agent['id']})")
                report.append(f"  - Capabilities: {', '.join(agent.get('capabilities', []))}")
                report.append("")
            
            # Add architecture analysis
            architecture_analysis = self.analysis_results.get("architecture", "Architecture analysis not available.")
            report.append("## Architecture Analysis")
            report.append(architecture_analysis)
            report.append("")
            
            # Add performance analysis
            performance_analysis = self.analysis_results.get("performance", "Performance analysis not available.")
            report.append("## Performance Analysis")
            report.append(performance_analysis)
            report.append("")
            
            # Add agent metrics
            agent_metrics = self.analysis_results.get("agent_metrics", {})
            if agent_metrics:
                report.append("## Agent Metrics")
                report.append("")
                for agent_id, data in agent_metrics.items():
                    metrics = data.get("metrics", {})
                    report.append(f"### {data.get('name')} ({data.get('type')})")
                    report.append(f"- Uptime: {metrics.get('uptime_formatted', 'N/A')}")
                    report.append(f"- Tasks Processed: {metrics.get('tasks_processed', 0)}")
                    report.append(f"- Success Rate: {metrics.get('success_rate', 0):.1f}%")
                    report.append(f"- Fallback Rate: {metrics.get('fallback_rate', 0):.1f}%")
                    report.append(f"- Average Response Time: {metrics.get('average_response_time', 0):.2f} seconds")
                    report.append("")
                    task_types = metrics.get("task_types", {})
                    if task_types:
                        report.append("#### Task Type Performance")
                        report.append("")
                        report.append("| Task Type | Count | Success Rate | Avg Time (s) |")
                        report.append("|-----------|-------|--------------|-------------|")
                        
                        for task_type, stats in task_types.items():
                            report.append(f"| {task_type} | {stats.get('count', 0)} | {stats.get('success_rate', 0):.1f}% | {stats.get('average_time', 0):.2f} |")
                        
                        report.append("")
            else:
                report.append("No agent metrics available.")
                report.append("")
            
            # Add recommendations
            recommendations = self.analysis_results.get("recommendations", "")
            if recommendations:
                report.append("## Recommendations for Improvement")
                report.append("")
                report.append(recommendations)
            else:
                report.append("No recommendations available.")
                report.append("")
            
            # Write the report to file
            with open(self.output_file, 'w') as f:
                f.write("\n".join(report))
            
            logger.info(f"Successfully wrote report to {self.output_file}")
            return True
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return False
    
    def cleanup(self) -> bool:
        """
        Clean up resources created for analysis.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.dev_agent_id:
            logger.info("No specialized agent to clean up")
            return True
        
        try:
            logger.info(f"Deleting specialized agent {self.dev_agent_id}...")
            response = requests.delete(f"{self.base_url}/api/agents/{self.dev_agent_id}")
            
            if response.status_code == 200:
                logger.info("Agent deleted successfully")
                self.dev_agent_id = None
                return True
            else:
                logger.error(f"Failed to delete agent: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error deleting agent: {e}")
            return False
    
    def run_analysis(self) -> Dict[str, bool]:
        """
        Run the full ecosystem analysis.
        
        Returns:
            Dict mapping analysis steps to success status
        """
        results = {}
        
        # Verify server
        results["server_verified"] = self.verify_server()
        if not results["server_verified"]:
            logger.error("Server verification failed, stopping analysis")
            return results
        
        # Get all agents
        results["agents_retrieved"] = self.get_all_agents()
        if not results["agents_retrieved"]:
            logger.warning("Failed to retrieve agents, continuing with limited analysis")
        
        # Create specialized agent
        results["agent_created"] = self.create_development_agent()
        if not results["agent_created"]:
            logger.error("Agent creation failed, stopping analysis")
            return results
        
        # Collect agent metrics
        results["metrics_collected"] = self.analyze_agent_metrics()
        
        # Analyze architecture
        results["architecture_analyzed"] = self.analyze_ecosystem_architecture()
        
        # Analyze performance
        results["performance_analyzed"] = self.analyze_performance()
        
        # Generate recommendations
        results["recommendations_generated"] = self.generate_recommendations()
        
        # Generate report
        results["report_generated"] = self.generate_report()
        
        # Cleanup
        results["cleanup"] = self.cleanup()
        
        return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MCP Agent Ecosystem Analyzer")
    parser.add_argument("--host", default="localhost", help="Host where the server is running")
    parser.add_argument("--port", type=int, default=5678, help="Port where the server is running")
    parser.add_argument("--output", default="ecosystem_analysis_report.md", 
                        help="Output file path for the analysis report")
    
    args = parser.parse_args()
    
    logger.info("========== STARTING MCP AGENT ECOSYSTEM ANALYSIS ==========")
    
    analyzer = EcosystemAnalyzer(host=args.host, port=args.port, output_file=args.output)
    results = analyzer.run_analysis()
    
    logger.info("========== ANALYSIS RESULTS ==========")
    all_passed = True
    for step, passed in results.items():
        logger.info(f"{step}: {'PASSED' if passed else 'FAILED'}")
        if not passed:
            all_passed = False
    
    logger.info("========== END OF ANALYSIS ==========")
    
    if results.get("report_generated", False):
        logger.info(f"Analysis report available at: {analyzer.output_file}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 