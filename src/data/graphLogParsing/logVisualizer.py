#!/usr/bin/env python3
"""
Generic Log Gantt Chart Generator

A tool to parse structured logs and generate Gantt charts showing execution timelines.
Designed to handle various log formats with timing information.

Usage:
    generator = LogGanttGenerator()
    fig = generator.generate_from_text(log_json_string)
    plt.show()
"""
# Add this RIGHT AFTER your docstring, BEFORE any matplotlib imports
import sys
import matplotlib
import os

# Simple backend configuration for PyCharm
if 'pydevd' in sys.modules:  # Detects PyCharm
    try:
        matplotlib.use('TkAgg')  # Try interactive backend first
        print("Using TkAgg backend for PyCharm")
    except ImportError:
        matplotlib.use('Agg')   # Fallback to file-saving backend
        print("Using Agg backend - plots will be saved to files")

# Your existing imports stay exactly the same below this point
# ... rest of your imports
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
from matplotlib.pyplot import cm
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from pathlib import Path
from abc import ABC, abstractmethod
from enum import Enum
import argparse


def show_plot(fig, title="chart"):
    """Show plot or save it if in non-interactive environment."""
    backend = matplotlib.get_backend()
    print(f"🔍 DEBUG: Current backend is: {backend}")
    print(f"🔍 DEBUG: PyCharm detected: {'pydevd' in sys.modules}")
    print(f"🔍 DEBUG: Title: {title}")

    if backend == 'Agg':
        # Save to file instead of showing
        filename = f"{title.replace(' ', '_').replace('/', '_')}.png"
        print(f"🔍 DEBUG: Attempting to save as: {filename}")

        try:
            fig.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"📊 SUCCESS: Plot saved as: {filename}")
            print(f"   📁 You can find it in: {os.getcwd()}")

            # Check if file actually exists
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                print(f"   ✅ File confirmed: {file_size} bytes")
            else:
                print(f"   ❌ ERROR: File was not created!")

        except Exception as e:
            print(f"   ❌ ERROR saving file: {e}")
    else:
        print(f"🔍 DEBUG: Attempting to show plot with backend: {backend}")
        try:
            plt.show()
            print("📊 Plot displayed successfully")
        except Exception as e:
            print(f"❌ ERROR showing plot: {e}")
            # Fallback to saving
            filename = f"{title.replace(' ', '_').replace('/', '_')}.png"
            fig.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"📊 FALLBACK: Plot saved as: {filename}")


# ================================
# DATA STRUCTURES
# ================================

@dataclass
class TimingEvent:
    """Represents a single timing event in the execution flow"""
    name: str
    service_name: str
    offset_ms: int
    latency_ms: int
    status: int
    method: str
    path: str
    event_type: str  # 'downstream', 'subgraph', 'internal'
    span_id: Optional[str] = None

    @property
    def start_time(self) -> int:
        return self.offset_ms

    @property
    def end_time(self) -> int:
        return self.offset_ms + self.latency_ms


class ChartStyle(Enum):
    """Different visual styles for the Gantt chart"""
    CLASSIC = "classic"
    MODERN = "modern"
    MINIMAL = "minimal"


@dataclass
class VisualizationConfig:
    """Configuration for Gantt chart visualization"""
    figsize: Tuple[int, int] = (14, 8)
    bar_height: float = 0.6
    style: ChartStyle = ChartStyle.MODERN
    show_labels: bool = True
    show_grid: bool = True
    group_parallel: bool = True
    color_by_service: bool = True


# ================================
# LOG PARSING COMPONENTS
# ================================

class LogFieldExtractor(ABC):
    """Abstract base for extracting fields from different log formats"""

    @abstractmethod
    def extract_service_name(self, event: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def extract_timing(self, event: Dict[str, Any]) -> Tuple[int, int]:  # offset, latency
        pass

    @abstractmethod
    def extract_request_details(self, event: Dict[str, Any]) -> Tuple[str, str, int]:  # method, path, status
        pass


class StandardLogExtractor(LogFieldExtractor):
    """Extractor that handles multiple log format variations"""

    def extract_service_name(self, event: Dict[str, Any]) -> str:
        return event.get('service_name', 'unknown')

    def extract_timing(self, event: Dict[str, Any]) -> Tuple[int, int]:
        """Extract offset and latency, handling multiple field name conventions"""

        # Try different offset field names
        offset = (event.get('offset_ms', 0) or
                  event.get('offset', 0) or
                  0)

        # Try different latency field names - THIS IS THE KEY FIX!
        latency = (event.get('latency_ms', 0) or
                   event.get('downstream_ms', 0) or  # Your first log format uses this
                   event.get('duration_ms', 0) or
                   0)

        print(
            f"DEBUG: Extracting timing for {event.get('service_name', 'unknown')}: offset={offset}, latency={latency}")

        return offset, latency

    def extract_request_details(self, event: Dict[str, Any]) -> Tuple[str, str, int]:
        """Extract method, path, and status with flexible field handling"""

        # Handle method - try direct field or nested in type
        method = event.get('method', 'UNKNOWN')
        if method == 'UNKNOWN' and 'type' in event and isinstance(event['type'], dict):
            method = event['type'].get('method', 'UNKNOWN')

        method = method.upper()

        # Handle path - try direct field or nested in type
        path = event.get('path', '/')
        if path == '/' and 'type' in event and isinstance(event['type'], dict):
            path = event['type'].get('path', '/')

        # Handle status - try multiple locations
        status = 200  # default

        if 'status' in event:
            status = event['status']
        elif 'type' in event and isinstance(event['type'], dict):
            if 'code' in event['type']:
                status = event['type']['code']
            elif 'status' in event['type']:
                status = event['type']['status']

        return method, path, status


class GenericLogParser:
    """Generic parser that can handle various log formats"""

    def __init__(self, extractor: LogFieldExtractor = None):
        self.extractor = extractor or StandardLogExtractor()

    def parse_log_data(self, log_input: Union[str, Dict[str, Any]]) -> List[TimingEvent]:
        """Parse log data from JSON string or dict"""
        if isinstance(log_input, str):
            try:
                log_data = json.loads(log_input)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        else:
            log_data = log_input

        # Navigate to payload (handle different structures)
        payload = self._extract_payload(log_data)

        events = []

        # Extract downstream events
        downstream_events = payload.get('downstream_log', [])
        print(f"DEBUG: Found {len(downstream_events)} downstream events")
        for i, event in enumerate(downstream_events):
            print(f"DEBUG: Processing downstream event {i}: {event.get('service_name', 'unknown')}")
            timing_event = self._create_timing_event(event, 'downstream')
            if timing_event:
                events.append(timing_event)

        # Extract subgraph events
        subgraph_events = payload.get('subgraph_downstream_log', [])
        print(f"DEBUG: Found {len(subgraph_events)} subgraph events")
        for i, event in enumerate(subgraph_events):
            print(f"DEBUG: Processing subgraph event {i}: {event.get('service_name', 'unknown')}")
            timing_event = self._create_timing_event(event, 'subgraph')
            if timing_event:
                events.append(timing_event)

        print(f"DEBUG: Total events created: {len(events)}")
        return events

    def _extract_payload(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract the payload from various log structures"""
        # Try common payload locations
        if 'payload' in log_data:
            return log_data['payload']
        elif 'data' in log_data:
            return log_data['data']
        else:
            # Assume the whole thing is the payload
            return log_data

    def _create_timing_event(self, event: Dict[str, Any], event_type: str) -> Optional[TimingEvent]:
        """Create a TimingEvent from raw event data"""
        try:
            service_name = self.extractor.extract_service_name(event)
            offset_ms, latency_ms = self.extractor.extract_timing(event)
            method, path, status = self.extractor.extract_request_details(event)

            # Skip events with zero latency (they're not meaningful for visualization)
            if latency_ms <= 0:
                print(f"DEBUG: Skipping event with zero latency: {service_name}")
                return None

            # Create a meaningful name
            name = f"{service_name}:{method}:{path.split('/')[-1]}"

            timing_event = TimingEvent(
                name=name,
                service_name=service_name,
                offset_ms=offset_ms,
                latency_ms=latency_ms,
                status=status,
                method=method,
                path=path,
                event_type=event_type,
                span_id=event.get('span_id')
            )

            print(f"DEBUG: Created timing event: {service_name} at {offset_ms}ms for {latency_ms}ms")
            return timing_event

        except (KeyError, TypeError) as e:
            print(f"Warning: Could not parse event {event}: {e}")
            return None


# ================================
# VISUALIZATION COMPONENTS
# ================================

class GanttVisualizer:
    """Creates Gantt charts from timing events"""

    def __init__(self, config: VisualizationConfig = None):
        self.config = config or VisualizationConfig()
        self._service_colors = {}
        self._color_map = None

    def create_gantt_chart(self, events: List[TimingEvent], title: str = "Execution Timeline") -> plt.Figure:
        """Create a Gantt chart from timing events"""
        if not events:
            raise ValueError("No events to visualize")

        # Sort events by start time for better visualization
        sorted_events = sorted(events, key=lambda e: e.start_time)

        # Set up the plot
        fig, ax = plt.subplots(figsize=self.config.figsize)

        # Generate colors
        self._setup_colors(sorted_events)

        # Group events if requested
        if self.config.group_parallel:
            grouped_events = self._group_parallel_events(sorted_events)
            self._plot_grouped_events(ax, grouped_events)
        else:
            self._plot_sequential_events(ax, sorted_events)

        # Style the chart
        self._style_chart(ax, title, sorted_events)

        return fig

    def _setup_colors(self, events: List[TimingEvent]):
        """Set up color mapping for services"""
        if self.config.color_by_service:
            unique_services = list(set(event.service_name for event in events))
            self._color_map = cm.get_cmap('tab20')

            for i, service in enumerate(unique_services):
                self._service_colors[service] = self._color_map(i / len(unique_services))
        else:
            # Color by event type
            type_colors = {
                'downstream': '#3498db',
                'subgraph': '#e74c3c',
                'internal': '#2ecc71'
            }
            self._service_colors = type_colors

    def _get_event_color(self, event: TimingEvent) -> str:
        """Get color for an event"""
        if self.config.color_by_service:
            return self._service_colors.get(event.service_name, '#95a5a6')
        else:
            return self._service_colors.get(event.event_type, '#95a5a6')

    def _group_parallel_events(self, events: List[TimingEvent]) -> List[List[TimingEvent]]:
        """Group events that run in parallel"""
        if not events:
            return []

        # Sort by start time
        sorted_events = sorted(events, key=lambda e: e.start_time)
        groups = []
        current_group = [sorted_events[0]]

        for event in sorted_events[1:]:
            # Check if this event overlaps with any in the current group
            overlaps_current = any(
                self._events_overlap(event, existing)
                for existing in current_group
            )

            if overlaps_current:
                current_group.append(event)
            else:
                groups.append(current_group)
                current_group = [event]

        groups.append(current_group)
        return groups

    def _events_overlap(self, event1: TimingEvent, event2: TimingEvent) -> bool:
        """Check if two events overlap in time"""
        return (event1.start_time < event2.end_time and
                event1.end_time > event2.start_time)

    def _plot_grouped_events(self, ax: plt.Axes, event_groups: List[List[TimingEvent]]):
        """Plot events grouped by parallel execution"""
        y_position = 0
        y_labels = []

        for group in event_groups:
            if len(group) == 1:
                # Single event
                event = group[0]
                self._plot_single_event(ax, event, y_position)
                y_labels.append(self._create_event_label(event))
                y_position += 1
            else:
                # Parallel events - stack them
                group_start_y = y_position
                for event in sorted(group, key=lambda e: e.service_name):
                    self._plot_single_event(ax, event, y_position)
                    y_labels.append(self._create_event_label(event))
                    y_position += 1

                # Add group indicator
                self._add_group_indicator(ax, group, group_start_y, y_position - 1)

        ax.set_yticks(range(len(y_labels)))
        ax.set_yticklabels(y_labels)
        ax.invert_yaxis()  # Top to bottom execution order

    def _plot_sequential_events(self, ax: plt.Axes, events: List[TimingEvent]):
        """Plot events in simple sequential order"""
        y_labels = []

        for i, event in enumerate(events):
            self._plot_single_event(ax, event, i)
            y_labels.append(self._create_event_label(event))

        ax.set_yticks(range(len(y_labels)))
        ax.set_yticklabels(y_labels)
        ax.invert_yaxis()

    def _plot_single_event(self, ax: plt.Axes, event: TimingEvent, y_pos: int):
        """Plot a single timing event as a horizontal bar"""
        color = self._get_event_color(event)

        # Main bar
        bar = ax.barh(
            y_pos,
            event.latency_ms,
            left=event.start_time,
            height=self.config.bar_height,
            color=color,
            alpha=0.8,
            edgecolor='white',
            linewidth=0.5
        )

        # Add timing labels if requested
        if self.config.show_labels:
            # Duration label inside bar if there's space
            if event.latency_ms > 50:  # Only show if bar is wide enough
                ax.text(
                    event.start_time + event.latency_ms / 2,
                    y_pos,
                    f"{event.latency_ms}ms",
                    ha='center',
                    va='center',
                    fontsize=8,
                    fontweight='bold',
                    color='white'
                )

            # Start time label
            ax.text(
                event.start_time - 5,
                y_pos,
                f"{event.start_time}",
                ha='right',
                va='center',
                fontsize=7,
                color='gray'
            )

    def _create_event_label(self, event: TimingEvent) -> str:
        """Create a descriptive label for the event"""
        if len(event.path) > 30:
            path_display = "..." + event.path[-27:]
        else:
            path_display = event.path

        return f"{event.service_name}\n{event.method} {path_display}"

    def _add_group_indicator(self, ax: plt.Axes, group: List[TimingEvent], start_y: int, end_y: int):
        """Add visual indicator for parallel execution group"""
        if len(group) <= 1:
            return

        # Find the time span of the group
        min_start = min(event.start_time for event in group)
        max_end = max(event.end_time for event in group)

        # Add a subtle background highlight
        ax.axvspan(
            min_start - 2,
            max_end + 2,
            ymin=(start_y - 0.4) / (end_y + 1),
            ymax=(end_y + 0.4) / (end_y + 1),
            alpha=0.1,
            color='orange',
            zorder=0
        )

    def _style_chart(self, ax: plt.Axes, title: str, events: List[TimingEvent]):
        """Apply styling to the chart"""
        ax.set_xlabel("Time (milliseconds)", fontsize=12, fontweight='bold')
        ax.set_ylabel("Service Operations", fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        if self.config.show_grid:
            ax.grid(True, axis='x', linestyle='--', alpha=0.3)
            ax.set_axisbelow(True)

        # Set x-axis formatting
        max_time = max(event.end_time for event in events)
        ax.set_xlim(0, max_time * 1.1)

        # Dynamic tick spacing
        if max_time < 100:
            tick_spacing = 10
        elif max_time < 1000:
            tick_spacing = 50
        else:
            tick_spacing = 100

        ax.xaxis.set_major_locator(ticker.MultipleLocator(tick_spacing))

        # Create legend if coloring by service
        if self.config.color_by_service and len(self._service_colors) > 1:
            legend_elements = [
                mpatches.Patch(color=color, label=service)
                for service, color in self._service_colors.items()
            ]
            ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1))

        plt.tight_layout()


# ================================
# MAIN ORCHESTRATOR
# ================================

class LogGanttGenerator:
    """Main orchestrator for generating Gantt charts from logs"""

    def __init__(self,
                 parser: Optional[GenericLogParser] = None,
                 visualizer: Optional[GanttVisualizer] = None):
        """
        Initialize the generator with optional custom components.

        This design allows for dependency injection - you can provide
        custom parsers or visualizers for different log formats.
        """
        self.parser = parser or GenericLogParser()
        self.visualizer = visualizer or GanttVisualizer()

    def generate_from_text(self, log_text: str, title: Optional[str] = None) -> plt.Figure:
        """
        Generate Gantt chart from log text.

        Args:
            log_text: JSON string containing log data
            title: Optional title for the chart

        Returns:
            matplotlib Figure object

        Raises:
            ValueError: If log parsing fails
            RuntimeError: If visualization fails
        """
        try:
            # Parse the log
            events = self.parser.parse_log_data(log_text)

            if not events:
                raise ValueError("No timing events found in log data")

            # Generate title if not provided
            if title is None:
                title = self._generate_title(log_text, events)

            # Create visualization
            return self.visualizer.create_gantt_chart(events, title)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in log data: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to generate Gantt chart: {e}")

    def generate_from_file(self, file_path: Union[str, Path], title: Optional[str] = None) -> plt.Figure:
        """Generate Gantt chart from log file"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Log file not found: {file_path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                log_text = f.read()

            return self.generate_from_text(log_text, title or f"Timeline from {path.name}")

        except Exception as e:
            raise RuntimeError(f"Failed to read or process file {file_path}: {e}")

    def generate_with_config(self,
                             log_text: str,
                             config: VisualizationConfig,
                             title: Optional[str] = None) -> plt.Figure:
        """Generate chart with custom visualization configuration"""
        # Create a new visualizer with the specified config
        custom_visualizer = GanttVisualizer(config)

        # Temporarily use the custom visualizer
        original_visualizer = self.visualizer
        self.visualizer = custom_visualizer

        try:
            return self.generate_from_text(log_text, title)
        finally:
            # Restore original visualizer
            self.visualizer = original_visualizer

    def analyze_log(self, log_text: str) -> Dict[str, Any]:
        """
        Analyze log without generating chart - useful for debugging.

        Returns summary statistics and event details.
        """
        try:
            events = self.parser.parse_log_data(log_text)

            if not events:
                return {"error": "No events found"}

            # Calculate statistics
            total_time = max(event.end_time for event in events)
            service_counts = {}
            event_type_counts = {}

            for event in events:
                service_counts[event.service_name] = service_counts.get(event.service_name, 0) + 1
                event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1

            # Find parallel operations
            parallel_groups = self._find_parallel_groups(events)

            return {
                "total_events": len(events),
                "total_execution_time_ms": total_time,
                "services": service_counts,
                "event_types": event_type_counts,
                "parallel_groups_count": len(parallel_groups),
                "longest_operation": max(events, key=lambda e: e.latency_ms),
                "critical_path_time": self._calculate_critical_path(events),
                "events": [
                    {
                        "name": e.name,
                        "service": e.service_name,
                        "start": e.start_time,
                        "duration": e.latency_ms,
                        "type": e.event_type
                    } for e in sorted(events, key=lambda e: e.start_time)
                ]
            }

        except Exception as e:
            return {"error": f"Analysis failed: {e}"}

    def _generate_title(self, log_text: str, events: List[TimingEvent]) -> str:
        """Generate a meaningful title from log data"""
        try:
            log_data = json.loads(log_text)
            payload = log_data.get('payload', {})

            operation_name = payload.get('operation_name', 'Unknown Operation')
            total_time = max(event.end_time for event in events) if events else 0

            return f"{operation_name} - Execution Timeline ({total_time}ms)"

        except:
            return "Service Execution Timeline"

    def _find_parallel_groups(self, events: List[TimingEvent]) -> List[List[TimingEvent]]:
        """Find groups of events that execute in parallel"""
        if not events:
            return []

        sorted_events = sorted(events, key=lambda e: e.start_time)
        parallel_groups = []

        for i, event1 in enumerate(sorted_events):
            group = [event1]

            for j, event2 in enumerate(sorted_events[i + 1:], i + 1):
                if self._events_overlap(event1, event2):
                    group.append(event2)

            if len(group) > 1:
                # Avoid duplicate groups
                group_key = tuple(sorted(e.name for e in group))
                if not any(tuple(sorted(g.name for g in existing)) == group_key
                           for existing in parallel_groups):
                    parallel_groups.append(group)

        return parallel_groups

    def _events_overlap(self, event1: TimingEvent, event2: TimingEvent) -> bool:
        """Check if two events overlap in time"""
        return (event1.start_time < event2.end_time and
                event1.end_time > event2.start_time)

    def _calculate_critical_path(self, events: List[TimingEvent]) -> int:
        """Calculate the critical path duration"""
        if not events:
            return 0

        # Simple critical path: sequence of non-overlapping longest operations
        sorted_events = sorted(events, key=lambda e: e.start_time)
        critical_path = 0
        last_end_time = 0

        for event in sorted_events:
            if event.start_time >= last_end_time:
                critical_path += event.latency_ms
                last_end_time = event.end_time
            else:
                # Overlapping event - take the longer duration
                overlap_duration = min(event.end_time, last_end_time) - event.start_time
                additional_time = max(0, event.end_time - last_end_time)
                critical_path += additional_time
                last_end_time = max(last_end_time, event.end_time)

        return critical_path


# ================================
# UTILITY FUNCTIONS
# ================================

def create_quick_chart(log_text: str,
                       style: str = "modern",
                       group_parallel: bool = True,
                       color_by_service: bool = True) -> plt.Figure:
    """
    Quick utility function for simple chart generation.

    Perfect for jupyter notebooks or simple scripts.
    """
    config = VisualizationConfig(
        style=ChartStyle(style),
        group_parallel=group_parallel,
        color_by_service=color_by_service
    )

    generator = LogGanttGenerator()
    return generator.generate_with_config(log_text, config)


# ================================
# DEMO AND TESTING
# ================================

def demo_with_your_log():
    """Demo using your actual log data"""

    # Your log data from the paste
    your_log = '''
    {
        "payload": {
            "event": "QUERY_OPERATION_COMPLETED",
            "operation_name": "FeedGroupNestedClients",
            "query_signature": "b773e7bd9cb91f6e6bc6832622652ccc196ce14a3ae5eba7b93941dba160f43a",
            "total_response_latency_ms": 818,
            "downstream_log": [
                {
                    "status": 200,
                    "service_name": "tokie",
                    "method": "get",
                    "path": "/signed/principals/current",
                    "span_id": "1b8938cfa0712ed3",
                    "offset_ms": 2,
                    "latency_ms": 20,
                    "subgraphErrors": [],
                    "timed_out": false
                },
                {
                    "status": 200,
                    "service_name": "Agraph-svc",
                    "method": "post",
                    "path": "/graphql",
                    "span_id": "f3920668bf68c341",
                    "offset_ms": 32,
                    "latency_ms": 780,
                    "subgraphErrors": [],
                    "timed_out": false
                }
            ],
            "subgraph_downstream_log": [
                {
                    "service_name": "grouper",
                    "offset_ms": 83,
                    "latency_ms": 15,
                    "subgraph_service_name": "graph-svc",
                    "type": {
                        "method": "GET",
                        "path": "/api/v2/group/92851732480",
                        "request_type": "HTTP",
                        "code": 200
                    }
                },
                {
                    "service_name": "hydrant",
                    "offset_ms": 104,
                    "latency_ms": 251,
                    "subgraph_service_name": "graph-svc",
                    "type": {
                        "method": "POST",
                        "path": "/api/v3/nested/networks/31234/feeds/group/92851732480",
                        "request_type": "HTTP",
                        "code": 200
                    }
                },
                {
                    "service_name": "hydrant",
                    "offset_ms": 105,
                    "latency_ms": 332,
                    "subgraph_service_name": "graph-svc",
                    "type": {
                        "method": "POST",
                        "path": "/api/v3/nested/networks/31234/feeds/group/92851732480",
                        "request_type": "HTTP",
                        "code": 200
                    }
                },
                {
                    "service_name": "hydrant",
                    "offset_ms": 443,
                    "latency_ms": 319,
                    "subgraph_service_name": "graph-svc",
                    "type": {
                        "method": "POST",
                        "path": "/api/v3/nested/threads/3334442462756864",
                        "request_type": "HTTP",
                        "code": 200
                    }
                },
                {
                    "service_name": "grouper",
                    "offset_ms": 784,
                    "latency_ms": 14,
                    "subgraph_service_name": "graph-svc",
                    "type": {
                        "method": "GET",
                        "path": "/api/v2/group_members/groups/92851732480",
                        "request_type": "HTTP",
                        "code": 200
                    }
                }
            ]
        }
    }
    '''

    print("=== Analyzing Your Log ===")
    generator = LogGanttGenerator()

    # First, let's analyze the log
    analysis = generator.analyze_log(your_log)
    print(f"Found {analysis['total_events']} events")
    print(f"Total execution time: {analysis['total_execution_time_ms']}ms")
    print(f"Services involved: {list(analysis['services'].keys())}")
    print(f"Parallel groups: {analysis['parallel_groups_count']}")

    # Generate the chart
    print("\n=== Generating Chart ===")
    fig = generator.generate_from_text(your_log)
    show_plot(fig, "FeedGroupNestedClients_Timeline")

    # Also show different visualization styles
    print("\n=== Different Styles ===")

    # Minimal style
    config_minimal = VisualizationConfig(
        style=ChartStyle.MINIMAL,
        color_by_service=False,
        group_parallel=False
    )
    fig_minimal = generator.generate_with_config(your_log, config_minimal, "Minimal Style")
    show_plot(fig_minimal, "Minimal_Style")


def test_basic_functionality():
    """Test basic functionality with minimal sample"""
    print("=== Testing Basic Functionality ===")

    simple_log = '''
    {
        "payload": {
            "operation_name": "TestOperation",
            "downstream_log": [
                {
                    "service_name": "service_a",
                    "method": "GET",
                    "path": "/api/test",
                    "offset_ms": 10,
                    "latency_ms": 50,
                    "status": 200
                },
                {
                    "service_name": "service_b", 
                    "method": "POST",
                    "path": "/api/data",
                    "offset_ms": 70,
                    "latency_ms": 30,
                    "status": 200
                }
            ]
        }
    }
    '''

    try:
        generator = LogGanttGenerator()
        events = generator.parser.parse_log_data(simple_log)
        print(f"✓ Parsed {len(events)} events successfully")

        analysis = generator.analyze_log(simple_log)
        print(f"✓ Analysis complete: {analysis['total_events']} events, {analysis['total_execution_time_ms']}ms total")

        fig = generator.generate_from_text(simple_log, "Test Chart")
        print("✓ Chart generated successfully")

        # Don't show plot in test, just verify it was created
        plt.close(fig)

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_from_input_file():
    """Test that loads JSON from input.json file for easy iteration"""
    print("=== Testing from input.json ===")

    input_file = "input.json"

    # Check if file exists
    if not os.path.exists(input_file):
        print(f"❌ {input_file} not found!")
        print(f"📝 Create {input_file} in the same folder and paste your JSON data there.")
        return False

    try:
        # Read the JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            log_text = f.read().strip()

        print(f"📁 Loaded {len(log_text)} characters from {input_file}")

        # Test parsing
        generator = LogGanttGenerator()
        events = generator.parser.parse_log_data(log_text)
        print(f"✓ Parsed {len(events)} events successfully")

        if not events:
            print("⚠️  No events found in the JSON - check your data format")
            return False

        # Show analysis
        analysis = generator.analyze_log(log_text)
        print(f"✓ Analysis complete: {analysis['total_events']} events, {analysis['total_execution_time_ms']}ms total")
        print(f"✓ Services involved: {list(analysis['services'].keys())}")
        print(f"✓ Event types: {list(analysis['event_types'].keys())}")

        # Generate charts
        print("\n=== Generating Charts ===")

        # Main chart
        fig = generator.generate_from_text(log_text)
        show_plot(fig, "input_file_chart")

        # Quick minimal chart too
        config_minimal = VisualizationConfig(
            style=ChartStyle.MINIMAL,
            color_by_service=False,
            group_parallel=False
        )
        fig_minimal = generator.generate_with_config(log_text, config_minimal, "Input File - Minimal")
        show_plot(fig_minimal, "input_file_minimal")

        print("✅ Success! Charts generated from input.json")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print("📝 Check that your input.json contains valid JSON")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_input_test():
    """Quick runner for the input file test"""
    print("=== Quick Input File Test ===")
    print(f"Backend: {matplotlib.get_backend()}")
    print(f"Working directory: {os.getcwd()}")
    print()

    success = test_from_input_file()

    if success:
        print("\n🎉 All good! Your JSON data is working perfectly.")
    else:
        print("\n❌ Something went wrong. Check the error messages above.")


def run_full_demo():
    """Run the full demo including backend detection and chart generation"""
    print("=== Backend Detection ===")
    print(f"PyCharm detected: {'pydevd' in sys.modules}")
    print(f"Current backend: {matplotlib.get_backend()}")

    # Run basic test first
    if test_basic_functionality():
        print("\n" + "=" * 50)
        # Then run demo with your log
        demo_with_your_log()
    else:
        print("Basic test failed, skipping demo")


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(description="Generate Gantt charts from structured logs")
    parser.add_argument("input", help="Input log file path or '-' for stdin")
    parser.add_argument("-o", "--output", help="Output image file path")
    parser.add_argument("-t", "--title", help="Chart title")
    parser.add_argument("--style", choices=["classic", "modern", "minimal"],
                        default="modern", help="Visual style")
    parser.add_argument("--no-group", action="store_true",
                        help="Don't group parallel operations")
    parser.add_argument("--color-by-type", action="store_true",
                        help="Color by event type instead of service")
    parser.add_argument("--analyze-only", action="store_true",
                        help="Only analyze log, don't generate chart")

    args = parser.parse_args()

    # Read input
    if args.input == "-":
        import sys
        log_text = sys.stdin.read()
    else:
        with open(args.input, 'r') as f:
            log_text = f.read()

    generator = LogGanttGenerator()

    if args.analyze_only:
        # Just analyze and print results
        analysis = generator.analyze_log(log_text)
        print(json.dumps(analysis, indent=2))
        return

    # Generate chart
    config = VisualizationConfig(
        style=ChartStyle(args.style),
        group_parallel=not args.no_group,
        color_by_service=not args.color_by_type
    )

    try:
        fig = generator.generate_with_config(log_text, config, args.title)

        if args.output:
            fig.savefig(args.output, dpi=300, bbox_inches='tight')
            print(f"Chart saved to {args.output}")
        else:
            plt.show()

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


# Add this so you can call the function directly
if __name__ == "__main__":
    # Check if we're being run directly vs via pytest
    if 'pytest' in sys.modules:
        # Being run by pytest - just do the test
        pass  # pytest will handle the test
    else:
        # Being run directly - do the full demo
        run_full_demo()