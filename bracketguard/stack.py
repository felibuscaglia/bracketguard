from typing import Optional


class Node:
    def __init__(self, value: str, position: tuple, next_node: object = None) -> None:
        self.value = value
        self.next = next_node
        self.position = position

class Stack:
    def __init__(self) -> None:
        self.top = None

    def push(self, value: str, line: int, col: int) -> None:
        self.top = Node(value=value, next_node=self.top, position=(col, line))
    
    def pop(self) -> Optional[object]:
        if self.top is None:
            return None
        
        prev_top = self.top
        self.top = self.top.next

        return prev_top
    
    def is_empty(self) -> bool:
        return self.top is None