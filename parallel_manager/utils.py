"""
File name:	utils.py
Created:	08/15/2023
Author:	Weili An
Email:	an107@purdue.edu
Version:	1.0 Initial Design Entry
Description:	Utility functions
"""

import logging
from typing import Any, Tuple, Dict


class LogAdapter(logging.LoggerAdapter):
    def process(self, msg: Any,
                kwargs: Dict[str, Any]) -> Tuple[Any, Dict[str, Any]]:
        return f"[{self.extra['name']}] {msg}", kwargs
