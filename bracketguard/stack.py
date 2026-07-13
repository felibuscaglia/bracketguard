from typing import Optional


class Node:
    def __init__(self, value: str, next_node: object = None) -> None:
        self.value = value
        self.next = next_node

class Stack:
    def __init__(self) -> None:
        self.top = None

    def push(self, value: str) -> None:
        self.top = Node(value=value, next_node=self.top)
    
    def pop(self) -> Optional[str]:
        if self.top is None:
            return None
        
        prev_top = self.top
        self.top = self.top.next

        return prev_top.value
    
    def is_empty(self) -> bool:
        return self.top is None