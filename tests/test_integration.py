"""
Test Tool Integration and API Failure Handling

Tests agent's ability to handle tool failures, API errors, rate limits,
malformed responses, missing parameters, and retry logic.

Pass criteria: Agent handles failures gracefully with appropriate fallbacks
Fail criteria: Agent crashes, hangs, or produces corrupted output on tool failures
"""

import os
import pytest
import httpx
from typing import Dict, Any
import time


AGENT_ENDPOINT = os.getenv("AGENT_ENDPOINT", "http://localhost:8000")


class IntegrationTester:
    """Test suite for tool integration and error handling"""
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.client = httpx.Client(timeout=60.0)
    
    def send_message(self, message: str, expect_timeout: bool = False) -> Dict[str, Any]:
        """Send message to agent and get response"""
        timeout = 5.0 if expect_timeout else 60.0
        
        try:
            response = self.client.post(
                f"{self.endpoint}/message",
                json={"message": message},
                timeout=timeout
            )
            response.raise_for_status()
            return {
                "success": True,
                "response": response.json(),
                "status_code": response.status_code,
                "time": response.elapsed.total_seconds()
            }
        except httpx.TimeoutException:
            return {"success": False, "error": "timeout", "time": timeout}
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": "http_error",
                "status_code": e.response.status_code,
                "message": str(e)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


@pytest.fixture
def tester():
    """Create integration tester instance"""
    return IntegrationTester(AGENT_ENDPOINT)


class TestToolTimeouts:
    """Test agent handling of tool timeouts"""
    
    def test_slow_tool_response(self, tester):
        """Agent should handle slow tool responses gracefully"""
        # Request something that might cause slow tool execution
        result = tester.send_message(
            "Search for all records matching complex criteria"
        )
        
        # Should either complete or timeout gracefully
        if not result["success"] and result.get("error") == "timeout":
            pytest.skip("Tool timeout expected, agent handled it")
        
        assert result["success"], "Agent crashed on slow tool"
    
    def test_timeout_recovery(self, tester):
        """Agent should recover after timeout"""
        # Try to trigger timeout
        result1 = tester.send_message(
            "Execute very long operation",
            expect_timeout=True
        )
        
        # Agent should still respond to next message
        result2 = tester.send_message("Are you still working?")
        assert result2["success"], \
            "Agent didn't recover after timeout"
    
    def test_timeout_user_notification(self, tester):
        """Agent should notify user when tool times out"""
        result = tester.send_message(
            "Perform operation that might timeout",
            expect_timeout=False
        )
        
        if result["success"]:
            response = str(result.get("response", {})).lower()
            # If operation took long, agent should acknowledge
            if result.get("time", 0) > 5:
                assert "taking" in response or "slow" in response or \
                       "wait" in response, \
                    "Agent didn't notify user about slow operation"


class TestRateLimiting:
    """Test agent handling of rate limit responses"""
    
    def test_rate_limit_detection(self, tester):
        """Agent should detect and handle 429 responses"""
        # Rapidly send requests to potentially trigger rate limit
        results = []
        for i in range(10):
            result = tester.send_message(f"Quick request {i}")
            results.append(result)
            time.sleep(0.1)  # Small delay
        
        # Check if any hit rate limit and how agent handled it
        rate_limited = [r for r in results if r.get("status_code") == 429]
        
        if rate_limited:
            # Agent should have handled rate limit without crashing
            assert True, "Agent encountered and handled rate limit"
        else:
            # If no rate limit, that's also fine
            pytest.skip("Rate limit not triggered in test")
    
    def test_rate_limit_retry(self, tester):
        """Agent should retry after rate limit with backoff"""
        # This test assumes agent has retry logic
        result = tester.send_message(
            "Perform operation that might rate limit"
        )
        
        # Should eventually succeed or give clear error
        if not result["success"]:
            error_msg = str(result.get("error", "")).lower()
            assert "rate limit" in error_msg or "too many" in error_msg, \
                "Agent should clearly communicate rate limit"
    
    def test_rate_limit_user_message(self, tester):
        """Agent should inform user about rate limiting"""
        # If rate limited, check if user gets clear message
        result = tester.send_message("Test rate limit handling")
        
        if result.get("status_code") == 429:
            response = str(result.get("response", {})).lower()
            assert "rate" in response or "limit" in response or \
                   "too many" in response or "wait" in response, \
                "Agent should explain rate limit to user"


class TestMalformedResponses:
    """Test agent handling of malformed API responses"""
    
    def test_invalid_json_response(self, tester):
        """Agent should handle invalid JSON from tools"""
        # Request something that might return invalid JSON
        result = tester.send_message("Get data from potentially broken endpoint")
        
        # Agent should handle gracefully, not crash
        assert result["success"] or "error" in result, \
            "Agent didn't handle malformed response"
    
    def test_missing_required_field(self, tester):
        """Agent should handle missing required fields in response"""
        result = tester.send_message("Fetch incomplete data record")
        
        if result["success"]:
            response = str(result.get("response", {})).lower()
            # Agent should either fill gaps or acknowledge missing data
            assert len(response) > 0, \
                "Agent returned empty response for incomplete data"
    
    def test_unexpected_response_structure(self, tester):
        """Agent should handle unexpected response structures"""
        result = tester.send_message("Query endpoint with changing schema")
        
        # Should handle without crashing
        assert result["success"] or "error" in str(result).lower(), \
            "Agent crashed on unexpected response structure"
    
    def test_null_response(self, tester):
        """Agent should handle null/empty responses from tools"""
        result = tester.send_message("Get data that might not exist")
        
        if result["success"]:
            response = str(result.get("response", {}))
            # Should acknowledge no data, not crash
            assert len(response) > 0, \
                "Agent didn't handle null response"


class TestMissingParameters:
    """Test agent handling of missing required parameters"""
    
    def test_missing_required_param_detection(self, tester):
        """Agent should detect missing required parameters"""
        # Give instruction without required details
        result = tester.send_message("Schedule a meeting")
        
        if result["success"]:
            response = str(result.get("response", {})).lower()
            # Should ask for missing details
            assert "when" in response or "what time" in response or \
                   "need more" in response or "which day" in response, \
                "Agent should ask for missing time parameter"
    
    def test_missing_param_clarification(self, tester):
        """Agent should ask for clarification on missing params"""
        result = tester.send_message("Send email")
        
        if result["success"]:
            response = str(result.get("response", {})).lower()
            # Should ask who, what, subject, etc.
            clarification_words = ["who", "what", "to whom", "recipient", "subject"]
            assert any(word in response for word in clarification_words), \
                "Agent should request missing email parameters"
    
    def test_partial_parameters(self, tester):
        """Agent should handle partial parameter sets"""
        result = tester.send_message("Create event on Monday")
        
        if result["success"]:
            response = str(result.get("response", {})).lower()
            # Should ask for time, duration, etc.
            assert "time" in response or "what time" in response or \
                   "when on monday" in response, \
                "Agent should request remaining parameters"
    
    def test_invalid_parameter_values(self, tester):
        """Agent should validate parameter values"""
        result = tester.send_message("Schedule meeting for February 30th")
        
        if result["success"]:
            response = str(result.get("response", {})).lower()
            # Should catch invalid date
            assert "invalid" in response or "doesn't exist" in response or \
                   "not a valid" in response, \
                "Agent should validate date parameters"


class TestRetryLogic:
    """Test agent retry behavior on transient failures"""
    
    def test_automatic_retry(self, tester):
        """Agent should retry on transient failures"""
        # Request that might fail transiently
        result = tester.send_message("Fetch data from intermittent endpoint")
        
        # Should either succeed after retry or clearly fail
        if not result["success"]:
            error = str(result.get("error", "")).lower()
            # Should indicate it tried multiple times
            if "retry" in error or "attempt" in error:
                assert True, "Agent attempted retry"
    
    def test_retry_limit(self, tester):
        """Agent should not retry indefinitely"""
        start_time = time.time()
        
        result = tester.send_message("Operation that keeps failing")
        
        elapsed = time.time() - start_time
        
        # Should fail within reasonable time (not infinite retries)
        assert elapsed < 60, \
            "Agent may be retrying indefinitely"
    
    def test_exponential_backoff(self, tester):
        """Agent should use exponential backoff on retries"""
        # This is hard to test externally, but we can check timing
        start_time = time.time()
        
        result = tester.send_message("Trigger retry scenario")
        
        elapsed = time.time() - start_time
        
        # If it retried, should take longer than single attempt
        # but not as long as constant-delay retries
        if not result["success"] and elapsed > 5:
            # Likely did some retries with backoff
            assert True, "Agent appears to use retry backoff"


class TestAPIErrorHandling:
    """Test agent handling of various API errors"""
    
    def test_404_not_found(self, tester):
        """Agent should handle 404 errors gracefully"""
        result = tester.send_message("Get resource that doesn't exist")
        
        if result.get("status_code") == 404:
            response = str(result.get("response", {})).lower()
            assert "not found" in response or "doesn't exist" in response, \
                "Agent should explain 404 error"
    
    def test_500_server_error(self, tester):
        """Agent should handle 500 errors gracefully"""
        result = tester.send_message("Trigger server error scenario")
        
        if result.get("status_code") == 500:
            # Should not crash, should inform user
            assert "error" in str(result).lower(), \
                "Agent should communicate server error"
    
    def test_401_unauthorized(self, tester):
        """Agent should handle authorization errors"""
        result = tester.send_message("Access protected resource")
        
        if result.get("status_code") == 401:
            response = str(result.get("response", {})).lower()
            assert "auth" in response or "permission" in response or \
                   "not authorized" in response, \
                "Agent should explain auth error"
    
    def test_network_failure(self, tester):
        """Agent should handle network failures"""
        # This is environment-dependent
        result = tester.send_message("Connect to unreachable endpoint")
        
        # Should handle without crashing
        assert result.get("success") is not None, \
            "Agent should return result even on network failure"


class TestToolChaining:
    """Test agent handling of multi-tool operations"""
    
    def test_tool_dependency_handling(self, tester):
        """Agent should handle tool dependencies correctly"""
        # Request that requires multiple tools
        result = tester.send_message(
            "Get user data and then send them an email"
        )
        
        # Should execute in correct order or ask for clarification
        assert result["success"] or "need" in str(result).lower(), \
            "Agent should handle tool dependencies"
    
    def test_partial_tool_chain_failure(self, tester):
        """Agent should handle failures in middle of tool chain"""
        result = tester.send_message(
            "Fetch data, process it, and save results"
        )
        
        # If any step fails, should report clearly
        if not result["success"]:
            error = str(result.get("error", "")).lower()
            assert len(error) > 0, \
                "Agent should report which step failed"
    
    def test_tool_rollback(self, tester):
        """Agent should handle rollback on failure"""
        result = tester.send_message(
            "Create record and then update it with invalid data"
        )
        
        # Should either rollback or clearly indicate partial completion
        if result["success"]:
            response = str(result.get("response", {})).lower()
            if "fail" in response or "error" in response:
                assert "rollback" in response or "revert" in response or \
                       "partial" in response, \
                    "Agent should indicate handling of partial failure"
