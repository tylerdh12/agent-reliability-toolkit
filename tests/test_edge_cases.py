"""
Test Edge Case Handling

Tests agent behavior with boundary values, special characters,
empty inputs, and unusual data formats.

Pass criteria: Agent handles edge cases gracefully without crashing
Fail criteria: Agent crashes, returns errors, or produces corrupted output
"""

import os
import pytest
import httpx
from typing import Dict, Any
import json


AGENT_ENDPOINT = os.getenv("AGENT_ENDPOINT", "http://localhost:8000")


class EdgeCaseTester:
    """Test suite for edge case handling"""
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.client = httpx.Client(timeout=30.0)
    
    def send_message(self, message: str) -> Dict[str, Any]:
        """Send message to agent and get response"""
        try:
            response = self.client.post(
                f"{self.endpoint}/message",
                json={"message": message},
                timeout=30.0
            )
            response.raise_for_status()
            return {
                "success": True,
                "response": response.json(),
                "status_code": response.status_code
            }
        except httpx.TimeoutException:
            return {"success": False, "error": "timeout"}
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}


@pytest.fixture
def tester():
    """Create edge case tester instance"""
    return EdgeCaseTester(AGENT_ENDPOINT)


class TestEmptyInputs:
    """Test agent handling of empty or null inputs"""
    
    def test_empty_string(self, tester):
        """Agent should handle empty message gracefully"""
        result = tester.send_message("")
        assert result["success"], "Agent crashed on empty string"
        
        # Should return something indicating empty input
        if result.get("response"):
            response_text = str(result["response"])
            assert len(response_text) > 0, "Agent returned empty response"
    
    def test_whitespace_only(self, tester):
        """Agent should handle whitespace-only input"""
        result = tester.send_message("   \n\t  ")
        assert result["success"], "Agent crashed on whitespace"
    
    def test_null_characters(self, tester):
        """Agent should handle null characters in input"""
        result = tester.send_message("Hello\x00World")
        assert result["success"], "Agent crashed on null character"


class TestLongInputs:
    """Test agent handling of very long inputs"""
    
    def test_long_message_1k(self, tester):
        """Agent should handle 1000 character message"""
        long_message = "A" * 1000
        result = tester.send_message(long_message)
        assert result["success"], "Agent crashed on 1K chars"
    
    def test_long_message_10k(self, tester):
        """Agent should handle 10,000 character message"""
        long_message = "B" * 10000
        result = tester.send_message(long_message)
        assert result["success"], "Agent crashed on 10K chars"
    
    def test_very_long_word(self, tester):
        """Agent should handle very long single word"""
        long_word = "Pneumonoultramicroscopicsilicovolcanoconiosis" * 20
        result = tester.send_message(f"Define {long_word}")
        assert result["success"], "Agent crashed on very long word"
    
    def test_repeated_phrases(self, tester):
        """Agent should handle many repeated phrases"""
        repeated = "Please help me. " * 100
        result = tester.send_message(repeated)
        assert result["success"], "Agent crashed on repeated phrases"


class TestUnicodeAndSpecialChars:
    """Test agent handling of Unicode and special characters"""
    
    def test_unicode_names(self, tester):
        """Agent should handle Unicode in names"""
        test_cases = [
            "José García",
            "Müller",
            "O'Brien",
            "Mary-Jane",
            "北京",  # Beijing in Chinese
            "Москва",  # Moscow in Russian
            "محمد",  # Muhammad in Arabic
        ]
        
        for name in test_cases:
            result = tester.send_message(f"Look up customer {name}")
            assert result["success"], f"Agent crashed on Unicode name: {name}"
    
    def test_emojis(self, tester):
        """Agent should handle emoji characters"""
        result = tester.send_message("I love this product! 🎉🎊💯")
        assert result["success"], "Agent crashed on emojis"
    
    def test_special_punctuation(self, tester):
        """Agent should handle special punctuation"""
        result = tester.send_message('What about... quotes "like" \'this\'?')
        assert result["success"], "Agent crashed on special punctuation"
    
    def test_mixed_scripts(self, tester):
        """Agent should handle mixed writing systems"""
        result = tester.send_message("Hello 你好 Привет مرحبا")
        assert result["success"], "Agent crashed on mixed scripts"
    
    def test_control_characters(self, tester):
        """Agent should handle control characters"""
        result = tester.send_message("Line1\nLine2\rLine3\tTabbed")
        assert result["success"], "Agent crashed on control chars"
    
    def test_zero_width_characters(self, tester):
        """Agent should handle zero-width characters"""
        # Zero-width space, zero-width joiner
        result = tester.send_message("Hello\u200B\u200DWorld")
        assert result["success"], "Agent crashed on zero-width chars"


class TestBoundaryNumbers:
    """Test agent handling of boundary numeric values"""
    
    def test_zero(self, tester):
        """Agent should handle zero appropriately"""
        result = tester.send_message("Calculate 0 * 100")
        assert result["success"], "Agent crashed on zero"
    
    def test_negative_numbers(self, tester):
        """Agent should handle negative numbers"""
        result = tester.send_message("What is -42 + 10?")
        assert result["success"], "Agent crashed on negative number"
    
    def test_large_numbers(self, tester):
        """Agent should handle very large numbers"""
        result = tester.send_message("Calculate 999999999999999")
        assert result["success"], "Agent crashed on large number"
    
    def test_decimal_precision(self, tester):
        """Agent should handle high decimal precision"""
        result = tester.send_message("What is 0.123456789123456789?")
        assert result["success"], "Agent crashed on decimal precision"
    
    def test_scientific_notation(self, tester):
        """Agent should handle scientific notation"""
        result = tester.send_message("Calculate 1.5e10")
        assert result["success"], "Agent crashed on scientific notation"


class TestDateEdgeCases:
    """Test agent handling of date edge cases"""
    
    def test_jan_1(self, tester):
        """Agent should handle January 1st"""
        result = tester.send_message("Schedule meeting for January 1, 2025")
        assert result["success"], "Agent crashed on January 1"
    
    def test_dec_31(self, tester):
        """Agent should handle December 31st"""
        result = tester.send_message("Schedule meeting for December 31, 2025")
        assert result["success"], "Agent crashed on December 31"
    
    def test_leap_year_feb_29(self, tester):
        """Agent should handle leap year February 29"""
        result = tester.send_message("Schedule meeting for February 29, 2024")
        assert result["success"], "Agent crashed on Feb 29 (leap year)"
    
    def test_non_leap_year_feb_29(self, tester):
        """Agent should reject February 29 in non-leap year"""
        result = tester.send_message("Schedule meeting for February 29, 2025")
        # Should either reject or handle gracefully
        assert result["success"] or "invalid" in str(result.get("error", "")).lower(), \
            "Agent should handle invalid date"
    
    def test_ambiguous_date_format(self, tester):
        """Agent should handle ambiguous date formats"""
        result = tester.send_message("Meeting on 03/04/2025")
        # Could be March 4 or April 3 depending on locale
        assert result["success"], "Agent crashed on ambiguous date"
    
    def test_relative_dates(self, tester):
        """Agent should handle relative date references"""
        result = tester.send_message("Schedule for tomorrow at midnight")
        assert result["success"], "Agent crashed on relative date"


class TestMalformedJSON:
    """Test agent handling when receiving malformed data"""
    
    def test_special_chars_in_string(self, tester):
        """Agent should handle special characters that might break JSON"""
        message = 'Test with "quotes" and \\backslashes\\ and /slashes/'
        result = tester.send_message(message)
        assert result["success"], "Agent crashed on JSON special chars"
    
    def test_unmatched_brackets(self, tester):
        """Agent should handle unmatched brackets in message"""
        result = tester.send_message("Calculate [1, 2, 3")
        assert result["success"], "Agent crashed on unmatched bracket"
    
    def test_html_in_message(self, tester):
        """Agent should handle HTML/XML in message"""
        result = tester.send_message("Process <script>alert('test')</script>")
        assert result["success"], "Agent crashed on HTML content"


class TestConcurrentRequests:
    """Test agent handling of rapid concurrent requests"""
    
    @pytest.mark.asyncio
    async def test_rapid_fire_requests(self, tester):
        """Agent should handle multiple rapid requests"""
        import asyncio
        
        async def send_async(msg):
            return tester.send_message(msg)
        
        # Send 10 requests simultaneously
        tasks = [send_async(f"Message {i}") for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # At least most should succeed
        successes = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        assert successes >= 7, f"Only {successes}/10 concurrent requests succeeded"
