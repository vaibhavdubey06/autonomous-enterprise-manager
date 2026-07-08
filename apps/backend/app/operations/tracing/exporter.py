from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.operations.tracing.span import Span

class TraceExporter(ABC):
    @abstractmethod
    def export(self, trace_id: str, spans: List[Span]):
        pass
        
    @abstractmethod
    def export_span(self, span: Span):
        pass

class InMemoryTraceExporter(TraceExporter):
    def __init__(self):
        self.traces: Dict[str, List[Span]] = {}
        
    def export(self, trace_id: str, spans: List[Span]):
        # Keep for backwards compat if needed
        if trace_id not in self.traces:
            self.traces[trace_id] = []
        self.traces[trace_id].extend(spans)
        
    def export_span(self, span: Any):
        if isinstance(span, dict):
            trace_id = span.get("trace_id")
        else:
            trace_id = span.trace_id
            
        if not trace_id:
            return
        if trace_id not in self.traces:
            self.traces[trace_id] = []
        self.traces[trace_id].append(span)
        
    def get_all_traces(self) -> Dict[str, List[dict]]:
        result = {}
        for tid, spans in self.traces.items():
            result[tid] = []
            for s in spans:
                if isinstance(s, dict):
                    result[tid].append(s)
                else:
                    result[tid].append(s.to_dict())
        return result
    
    def clear(self):
        self.traces.clear()
