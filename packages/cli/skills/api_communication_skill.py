"""
API Communication Skill
Provides comprehensive API communication capabilities including HTTP requests,
authentication, rate limiting, and response processing.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

import aiohttp
import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from urllib3.util.retry import Retry

from .base_skill import BaseSkill, SkillParameter, SkillResult, SkillType


class APIAuthenticator:
    """Base class for API authentication methods"""

    def apply_auth(self, session, **kwargs):
        """Apply authentication to session or request"""
        pass


class BearerTokenAuth(APIAuthenticator):
    """Bearer token authentication"""

    def __init__(self, token: str):
        self.token = token

    def apply_auth(self, session, **kwargs):
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"
        kwargs["headers"] = headers
        return kwargs


class APIKeyAuth(APIAuthenticator):
    """API key authentication (header or query parameter)"""

    def __init__(
        self, api_key: str, location: str = "header", key_name: str = "X-API-Key"
    ):
        self.api_key = api_key
        self.location = location
        self.key_name = key_name

    def apply_auth(self, session, **kwargs):
        if self.location == "header":
            headers = kwargs.get("headers", {})
            headers[self.key_name] = self.api_key
            kwargs["headers"] = headers
        elif self.location == "query":
            params = kwargs.get("params", {})
            params[self.key_name] = self.api_key
            kwargs["params"] = params
        return kwargs


class RateLimiter:
    """Simple rate limiter for API requests"""

    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()

        # Remove old requests outside time window
        self.requests = [
            req_time for req_time in self.requests if now - req_time < self.time_window
        ]

        # If at limit, wait until oldest request expires
        if len(self.requests) >= self.max_requests:
            oldest_request = min(self.requests)
            wait_time = self.time_window - (now - oldest_request)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                # Remove expired requests after waiting
                now = time.time()
                self.requests = [
                    req_time
                    for req_time in self.requests
                    if now - req_time < self.time_window
                ]

        # Record this request
        self.requests.append(now)


class APICommunicationSkill(BaseSkill):
    """
    Skill for handling API communications and HTTP requests.
    Supports various authentication methods, rate limiting, retries, and response processing.
    """

    def __init__(
        self,
        skill_id: str = "api_communication_001",
        name: str = "API Communication",
        description: str = "Comprehensive API communication and HTTP request capabilities",
        version: str = "1.0.0",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the API Communication Skill.

        Args:
            skill_id: Unique skill identifier
            name: Skill name
            description: Skill description
            version: Skill version
            config: Configuration parameters
        """
        super().__init__(
            skill_id=skill_id,
            name=name,
            skill_type=SkillType.API_INTEGRATION,
            description=description,
            version=version,
            config=config or {},
        )

        # Default configuration
        default_config = {
            "timeout": 30,
            "max_retries": 3,
            "retry_delay": 1,
            "retry_backoff": 2,
            "user_agent": "API-Communication-Skill/1.0.0",
            "verify_ssl": True,
            "follow_redirects": True,
            "max_redirects": 10,
            "rate_limit_requests": 60,
            "rate_limit_window": 60,  # seconds
            "default_content_type": "application/json",
        }

        # Merge with provided config
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            self.config["rate_limit_requests"], self.config["rate_limit_window"]
        )

        # Session storage for reusing connections
        self.sessions = {}

        # Request/response history
        self.request_history = []

    async def execute(self, parameters: Dict[str, Any]) -> SkillResult:
        """
        Execute API communication operation.

        Args:
            parameters: Operation parameters including:
                - operation: Type of API operation
                - url: Target URL
                - method: HTTP method
                - Additional operation-specific parameters

        Returns:
            SkillResult with operation results
        """
        operation = parameters.get("operation", "request").lower()

        try:
            if operation == "request":
                return await self._make_request(parameters)
            elif operation == "batch_requests":
                return await self._batch_requests(parameters)
            elif operation == "upload_file":
                return await self._upload_file(parameters)
            elif operation == "download_file":
                return await self._download_file(parameters)
            elif operation == "stream_request":
                return await self._stream_request(parameters)
            elif operation == "websocket":
                return await self._websocket_connection(parameters)
            elif operation == "graphql":
                return await self._graphql_request(parameters)
            elif operation == "oauth_flow":
                return await self._oauth_flow(parameters)
            elif operation == "health_check":
                return await self._health_check(parameters)
            else:
                raise ValueError(f"Unsupported operation: {operation}")

        except Exception as e:
            return SkillResult(
                success=False,
                error=f"API operation '{operation}' failed: {str(e)}",
                skill_used=self.name,
            )

    async def _make_request(self, parameters: Dict[str, Any]) -> SkillResult:
        """Make HTTP request"""
        url = parameters["url"]
        method = parameters.get("method", "GET").upper()
        headers = parameters.get("headers", {})
        params = parameters.get("params", {})
        data = parameters.get("data", {})
        json_data = parameters.get("json", {})
        timeout = parameters.get("timeout", self.config["timeout"])
        auth_config = parameters.get("auth", {})
        use_rate_limit = parameters.get("use_rate_limit", True)

        # Apply rate limiting
        if use_rate_limit:
            await self.rate_limiter.wait_if_needed()

        # Set default headers
        default_headers = {
            "User-Agent": self.config["user_agent"],
            "Accept": "application/json",
        }
        headers = {**default_headers, **headers}

        # Apply authentication
        request_kwargs = {
            "headers": headers,
            "params": params,
            "timeout": timeout,
        }

        if auth_config:
            auth = self._create_authenticator(auth_config)
            if auth:
                request_kwargs = auth.apply_auth(None, **request_kwargs)

        # Add request body
        if json_data:
            request_kwargs["json"] = json_data
            request_kwargs["headers"]["Content-Type"] = "application/json"
        elif data:
            request_kwargs["data"] = data

        start_time = time.time()

        try:
            # Make request with retries
            response_data = await self._make_request_with_retries(
                method, url, **request_kwargs
            )

            execution_time = time.time() - start_time

            # Log request
            self.request_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "method": method,
                    "url": url,
                    "status_code": response_data.get("status_code"),
                    "execution_time": execution_time,
                    "success": True,
                }
            )

            return SkillResult(
                success=True,
                data=response_data,
                execution_time=execution_time,
                metadata={
                    "method": method,
                    "url": url,
                    "status_code": response_data.get("status_code"),
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time

            # Log failed request
            self.request_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "method": method,
                    "url": url,
                    "error": str(e),
                    "execution_time": execution_time,
                    "success": False,
                }
            )

            raise Exception(f"Request failed: {str(e)}")

    async def _make_request_with_retries(
        self, method: str, url: str, **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        last_exception = None

        for attempt in range(self.config["max_retries"] + 1):
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=kwargs.get("timeout", 30))
                ) as session:
                    async with session.request(method, url, **kwargs) as response:
                        response_data = {
                            "status_code": response.status,
                            "headers": dict(response.headers),
                            "url": str(response.url),
                            "cookies": dict(response.cookies),
                            "elapsed_time": 0,  # aiohttp doesn't provide this directly
                        }

                        # Try to parse response body
                        content_type = response.headers.get("content-type", "").lower()

                        if "application/json" in content_type:
                            try:
                                response_data["data"] = await response.json()
                                response_data["content_type"] = "json"
                            except:
                                response_data["data"] = await response.text()
                                response_data["content_type"] = "text"
                        elif "text/" in content_type:
                            response_data["data"] = await response.text()
                            response_data["content_type"] = "text"
                        else:
                            response_data["data"] = await response.read()
                            response_data["content_type"] = "binary"

                        # Check if response indicates success
                        if response.status >= 400:
                            raise aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status,
                                message=f"HTTP {response.status}",
                                headers=response.headers,
                            )

                        return response_data

            except Exception as e:
                last_exception = e

                # Don't retry on client errors (4xx)
                if hasattr(e, "status") and 400 <= e.status < 500:
                    break

                # Wait before retry
                if attempt < self.config["max_retries"]:
                    wait_time = self.config["retry_delay"] * (
                        self.config["retry_backoff"] ** attempt
                    )
                    await asyncio.sleep(wait_time)

        # All retries exhausted
        raise last_exception

    async def _batch_requests(self, parameters: Dict[str, Any]) -> SkillResult:
        """Make multiple requests concurrently"""
        requests_config = parameters["requests"]
        max_concurrent = parameters.get("max_concurrent", 10)
        delay_between_batches = parameters.get("delay", 0)

        all_results = []
        failed_requests = []

        # Process requests in batches
        for i in range(0, len(requests_config), max_concurrent):
            batch = requests_config[i : i + max_concurrent]

            # Create tasks for batch
            tasks = []
            for req_config in batch:
                req_config["operation"] = "request"
                task = self._make_request(req_config)
                tasks.append(task)

            # Execute batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    failed_requests.append(
                        {
                            "index": i + j,
                            "config": batch[j],
                            "error": str(result),
                        }
                    )
                elif result.success:
                    all_results.append(result.data)
                else:
                    failed_requests.append(
                        {
                            "index": i + j,
                            "config": batch[j],
                            "error": result.error,
                        }
                    )

            # Delay between batches
            if i + max_concurrent < len(requests_config) and delay_between_batches > 0:
                await asyncio.sleep(delay_between_batches)

        return SkillResult(
            success=True,
            data={
                "results": all_results,
                "successful_requests": len(all_results),
                "failed_requests": failed_requests,
                "success_rate": len(all_results) / len(requests_config) * 100,
            },
            metadata={
                "total_requests": len(requests_config),
                "batch_size": max_concurrent,
            },
        )

    async def _upload_file(self, parameters: Dict[str, Any]) -> SkillResult:
        """Upload file to API endpoint"""
        url = parameters["url"]
        file_path = parameters["file_path"]
        field_name = parameters.get("field_name", "file")
        additional_data = parameters.get("data", {})
        headers = parameters.get("headers", {})
        auth_config = parameters.get("auth", {})

        try:
            with open(file_path, "rb") as f:
                files = {field_name: f}
                data = additional_data

                # Apply authentication to headers
                if auth_config:
                    auth = self._create_authenticator(auth_config)
                    if auth:
                        request_kwargs = auth.apply_auth(None, headers=headers)
                        headers = request_kwargs.get("headers", headers)

                # Use requests for file upload (easier multipart handling)
                response = requests.post(
                    url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=self.config["timeout"],
                    verify=self.config["verify_ssl"],
                )

                response.raise_for_status()

                # Parse response
                try:
                    response_data = response.json()
                except:
                    response_data = response.text

                return SkillResult(
                    success=True,
                    data={
                        "status_code": response.status_code,
                        "response_data": response_data,
                        "file_path": file_path,
                        "upload_size": f.tell(),
                    },
                    metadata={
                        "operation": "upload_file",
                        "url": url,
                        "field_name": field_name,
                    },
                )

        except Exception as e:
            raise Exception(f"File upload failed: {str(e)}")

    async def _download_file(self, parameters: Dict[str, Any]) -> SkillResult:
        """Download file from API endpoint"""
        url = parameters["url"]
        file_path = parameters["file_path"]
        headers = parameters.get("headers", {})
        auth_config = parameters.get("auth", {})
        chunk_size = parameters.get("chunk_size", 8192)

        # Apply authentication
        request_kwargs = {"headers": headers}
        if auth_config:
            auth = self._create_authenticator(auth_config)
            if auth:
                request_kwargs = auth.apply_auth(None, **request_kwargs)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, **request_kwargs) as response:
                    response.raise_for_status()

                    total_size = int(response.headers.get("content-length", 0))
                    downloaded_size = 0

                    with open(file_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            f.write(chunk)
                            downloaded_size += len(chunk)

                    return SkillResult(
                        success=True,
                        data={
                            "file_path": file_path,
                            "downloaded_size": downloaded_size,
                            "total_size": total_size,
                            "content_type": response.headers.get("content-type"),
                        },
                        metadata={
                            "operation": "download_file",
                            "url": url,
                        },
                    )

        except Exception as e:
            raise Exception(f"File download failed: {str(e)}")

    async def _stream_request(self, parameters: Dict[str, Any]) -> SkillResult:
        """Handle streaming API requests"""
        url = parameters["url"]
        headers = parameters.get("headers", {})
        auth_config = parameters.get("auth", {})
        max_lines = parameters.get("max_lines", 100)
        timeout = parameters.get("timeout", 300)  # Longer timeout for streaming

        # Apply authentication
        request_kwargs = {"headers": headers}
        if auth_config:
            auth = self._create_authenticator(auth_config)
            if auth:
                request_kwargs = auth.apply_auth(None, **request_kwargs)

        try:
            streamed_data = []
            line_count = 0

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.get(url, **request_kwargs) as response:
                    response.raise_for_status()

                    async for line in response.content:
                        if line_count >= max_lines:
                            break

                        try:
                            # Try to parse as JSON (common for streaming APIs)
                            line_data = json.loads(line.decode("utf-8").strip())
                            streamed_data.append(line_data)
                        except:
                            # If not JSON, store as text
                            streamed_data.append(line.decode("utf-8").strip())

                        line_count += 1

            return SkillResult(
                success=True,
                data={
                    "streamed_data": streamed_data,
                    "lines_received": line_count,
                    "max_lines": max_lines,
                    "truncated": line_count >= max_lines,
                },
                metadata={
                    "operation": "stream_request",
                    "url": url,
                },
            )

        except Exception as e:
            raise Exception(f"Stream request failed: {str(e)}")

    async def _websocket_connection(self, parameters: Dict[str, Any]) -> SkillResult:
        """Handle WebSocket connections"""
        url = parameters["url"]
        messages_to_send = parameters.get("messages", [])
        max_receive = parameters.get("max_receive", 10)
        timeout = parameters.get("timeout", 30)

        try:
            import aiohttp

            received_messages = []

            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(url) as ws:
                    # Send messages
                    for message in messages_to_send:
                        if isinstance(message, dict):
                            await ws.send_json(message)
                        else:
                            await ws.send_str(str(message))

                    # Receive messages
                    count = 0
                    async for msg in ws:
                        if count >= max_receive:
                            break

                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                            except:
                                data = msg.data
                            received_messages.append(
                                {
                                    "type": "text",
                                    "data": data,
                                    "timestamp": datetime.now().isoformat(),
                                }
                            )
                        elif msg.type == aiohttp.WSMsgType.BINARY:
                            received_messages.append(
                                {
                                    "type": "binary",
                                    "data": msg.data.hex(),
                                    "timestamp": datetime.now().isoformat(),
                                }
                            )
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break

                        count += 1

            return SkillResult(
                success=True,
                data={
                    "sent_messages": len(messages_to_send),
                    "received_messages": received_messages,
                    "message_count": len(received_messages),
                },
                metadata={
                    "operation": "websocket",
                    "url": url,
                },
            )

        except Exception as e:
            raise Exception(f"WebSocket connection failed: {str(e)}")

    async def _graphql_request(self, parameters: Dict[str, Any]) -> SkillResult:
        """Make GraphQL request"""
        url = parameters["url"]
        query = parameters["query"]
        variables = parameters.get("variables", {})
        operation_name = parameters.get("operation_name")
        headers = parameters.get("headers", {})
        auth_config = parameters.get("auth", {})

        # Prepare GraphQL request
        graphql_request = {
            "query": query,
            "variables": variables,
        }

        if operation_name:
            graphql_request["operationName"] = operation_name

        # Make request using the standard request method
        request_params = {
            "operation": "request",
            "url": url,
            "method": "POST",
            "json": graphql_request,
            "headers": {**headers, "Content-Type": "application/json"},
            "auth": auth_config,
        }

        result = await self._make_request(request_params)

        # Process GraphQL-specific response
        if (
            result.success
            and "data" in result.data
            and isinstance(result.data["data"], dict)
        ):
            graphql_data = result.data["data"].get("data")
            graphql_errors = result.data["data"].get("errors", [])

            result.data["graphql_data"] = graphql_data
            result.data["graphql_errors"] = graphql_errors
            result.data["has_errors"] = len(graphql_errors) > 0

        result.metadata["operation"] = "graphql"
        result.metadata["query_length"] = len(query)

        return result

    async def _oauth_flow(self, parameters: Dict[str, Any]) -> SkillResult:
        """Handle OAuth 2.0 flow"""
        grant_type = parameters[
            "grant_type"
        ]  # client_credentials, authorization_code, etc.
        token_url = parameters["token_url"]
        client_id = parameters["client_id"]
        client_secret = parameters["client_secret"]

        token_data = {
            "grant_type": grant_type,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        # Add flow-specific parameters
        if grant_type == "authorization_code":
            token_data["code"] = parameters["code"]
            token_data["redirect_uri"] = parameters.get("redirect_uri")
        elif grant_type == "refresh_token":
            token_data["refresh_token"] = parameters["refresh_token"]

        if "scope" in parameters:
            token_data["scope"] = parameters["scope"]

        # Make token request
        request_params = {
            "operation": "request",
            "url": token_url,
            "method": "POST",
            "data": token_data,
            "headers": {"Content-Type": "application/x-www-form-urlencoded"},
        }

        result = await self._make_request(request_params)

        if result.success:
            token_response = result.data.get("data", {})
            result.data["oauth_token"] = token_response.get("access_token")
            result.data["token_type"] = token_response.get("token_type", "Bearer")
            result.data["expires_in"] = token_response.get("expires_in")
            result.data["refresh_token"] = token_response.get("refresh_token")
            result.data["scope"] = token_response.get("scope")

        result.metadata["operation"] = "oauth_flow"
        result.metadata["grant_type"] = grant_type

        return result

    async def _health_check(self, parameters: Dict[str, Any]) -> SkillResult:
        """Perform API health check"""
        urls = (
            parameters["urls"]
            if isinstance(parameters["urls"], list)
            else [parameters["urls"]]
        )
        timeout = parameters.get("timeout", 10)

        health_results = []

        for url in urls:
            start_time = time.time()
            try:
                request_params = {
                    "operation": "request",
                    "url": url,
                    "method": "GET",
                    "timeout": timeout,
                    "use_rate_limit": False,
                }

                result = await self._make_request(request_params)
                response_time = time.time() - start_time

                health_results.append(
                    {
                        "url": url,
                        "status": "healthy" if result.success else "unhealthy",
                        "status_code": result.data.get("status_code")
                        if result.success
                        else None,
                        "response_time": response_time,
                        "error": None if result.success else result.error,
                    }
                )

            except Exception as e:
                response_time = time.time() - start_time
                health_results.append(
                    {
                        "url": url,
                        "status": "unhealthy",
                        "status_code": None,
                        "response_time": response_time,
                        "error": str(e),
                    }
                )

        overall_health = all(result["status"] == "healthy" for result in health_results)

        return SkillResult(
            success=True,
            data={
                "overall_health": "healthy" if overall_health else "unhealthy",
                "results": health_results,
                "healthy_endpoints": sum(
                    1 for r in health_results if r["status"] == "healthy"
                ),
                "total_endpoints": len(health_results),
            },
            metadata={
                "operation": "health_check",
                "endpoints_checked": len(urls),
            },
        )

    def _create_authenticator(
        self, auth_config: Dict[str, Any]
    ) -> Optional[APIAuthenticator]:
        """Create appropriate authenticator based on config"""
        auth_type = auth_config.get("type", "").lower()

        if auth_type == "bearer":
            return BearerTokenAuth(auth_config["token"])
        elif auth_type == "api_key":
            return APIKeyAuth(
                auth_config["api_key"],
                auth_config.get("location", "header"),
                auth_config.get("key_name", "X-API-Key"),
            )
        # Note: Basic and Digest auth would need to be handled differently with aiohttp

        return None

    def get_request_history(self) -> List[Dict[str, Any]]:
        """Get request history"""
        return self.request_history.copy()

    def clear_history(self):
        """Clear request history"""
        self.request_history.clear()

    def get_parameters(self) -> List[SkillParameter]:
        """Get list of parameters this skill accepts"""
        return [
            SkillParameter(
                name="operation",
                param_type=str,
                required=True,
                description="Type of API operation to perform",
            ),
            SkillParameter(
                name="url",
                param_type=str,
                required=True,
                description="Target URL for the API request",
            ),
            SkillParameter(
                name="method",
                param_type=str,
                required=False,
                default="GET",
                description="HTTP method (GET, POST, PUT, DELETE, etc.)",
            ),
            SkillParameter(
                name="headers",
                param_type=dict,
                required=False,
                default={},
                description="HTTP headers to include in the request",
            ),
            SkillParameter(
                name="params",
                param_type=dict,
                required=False,
                default={},
                description="URL parameters",
            ),
            SkillParameter(
                name="data",
                param_type=dict,
                required=False,
                default={},
                description="Request body data (form data)",
            ),
            SkillParameter(
                name="json",
                param_type=dict,
                required=False,
                default={},
                description="JSON request body",
            ),
            SkillParameter(
                name="auth",
                param_type=dict,
                required=False,
                description="Authentication configuration",
            ),
            SkillParameter(
                name="timeout",
                param_type=int,
                required=False,
                default=30,
                description="Request timeout in seconds",
            ),
            SkillParameter(
                name="use_rate_limit",
                param_type=bool,
                required=False,
                default=True,
                description="Whether to apply rate limiting",
            ),
        ]
