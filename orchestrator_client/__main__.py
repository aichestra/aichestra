import asyncio
import base64
import os
import urllib.parse
import httpx
import json
from uuid import uuid4

import asyncclick as click

from a2a.client import A2AClient, A2ACardResolver
from a2a.types import (
    Part,
    TextPart,
    FilePart,
    FileWithBytes,
    Task,
    TaskState,
    Message,
    Role,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    MessageSendConfiguration,
    SendMessageRequest,
    SendStreamingMessageRequest,
    MessageSendParams,
    GetTaskRequest,
    TaskQueryParams,
    JSONRPCErrorResponse,
)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.push_notification_auth import PushNotificationReceiverAuth


def format_ai_response(content):
    """Format AI response for better readability."""
    if isinstance(content, dict):
        # Handle A2A task artifacts (from orchestrator)
        if 'artifacts' in content:
            artifacts = content.get('artifacts', [])
            if artifacts:
                for artifact in artifacts:
                    parts = artifact.get('parts', [])
                    for part in parts:
                        if part.get('kind') == 'text':
                            text = part.get('text', '')
                            # Extract just the final answer from orchestrator response
                            if '→' in text:
                                # Split on → and take the part after it
                                answer = text.split('→', 1)[-1].strip()
                                print("\n" + "="*60)
                                print("🤖 AI RESPONSE")
                                print("="*60)
                                print(answer)
                                print("="*60)
                                return True
                            else:
                                print("\n" + "="*60)
                                print("🤖 AI RESPONSE")
                                print("="*60)
                                print(text)
                                print("="*60)
                                return True
        
        # Handle structured data
        if 'content' in content:
            ai_content = content['content']
            if isinstance(ai_content, dict):
                # Handle task list from planner
                if 'tasks' in ai_content:
                    print("\n" + "="*60)
                    print("🤖 AI PLANNER RESPONSE")
                    print("="*60)
                    print(f"Original Query: {ai_content.get('original_query', 'N/A')}")
                    print(f"Task Type: {ai_content.get('task_info', {}).get('task_type', 'N/A')}")
                    print(f"Scope: {ai_content.get('task_info', {}).get('scope', 'N/A')}")
                    print("\n📋 TASKS:")
                    for task in ai_content.get('tasks', []):
                        print(f"  • Task {task.get('id', 'N/A')}: {task.get('description', 'N/A')}")
                        print(f"    Status: {task.get('status', 'N/A')}")
                    print("="*60)
                    return True
                else:
                    # Handle other structured content
                    print("\n" + "="*60)
                    print("🤖 AI RESPONSE")
                    print("="*60)
                    for key, value in ai_content.items():
                        if key != 'content':  # Avoid nested content
                            print(f"{key}: {value}")
                    print("="*60)
                    return True
            elif isinstance(ai_content, str):
                # Handle text content
                print("\n" + "="*60)
                print("🤖 AI RESPONSE")
                print("="*60)
                print(ai_content)
                print("="*60)
                return True
    elif isinstance(content, str):
        # Handle direct string content
        print("\n" + "="*60)
        print("🤖 AI RESPONSE")
        print("="*60)
        print(content)
        print("="*60)
        return True
    
    return False


async def list_available_agents(httpx_client, agent_url: str, card):
    """List available agents if connecting to orchestrator"""
    try:
        # Check if this is the orchestrator by looking at the agent card
        if "orchestrator" in card.name.lower() or "routing" in card.description.lower():
            print("\n" + "="*60)
            print("🤖 AVAILABLE AGENTS")
            print("="*60)
            
            # Get agents from orchestrator via API call
            available_agents = await get_agents_from_orchestrator(httpx_client, agent_url)
            
            if available_agents:
                print(f"Found {len(available_agents)} available agents:")
                for i, agent in enumerate(available_agents, 1):
                    print(f"\n{i}. {agent['name']} ({agent['endpoint']})")
                    print(f"   Description: {agent['description']}")
                    if agent['skills']:
                        skills_text = ", ".join([skill.get('name', 'Unknown') for skill in agent['skills'][:3]])
                        if len(agent['skills']) > 3:
                            skills_text += f" (+{len(agent['skills'])-3} more)"
                        print(f"   Skills: {skills_text}")
                print("\n" + "="*60)
                print("💡 The orchestrator will automatically route your requests to the best agent!")
            else:
                print("⚠️  No agents currently available")
            print("="*60)
    except Exception as e:
        # Silently fail if we can't get agent info
        pass


async def send_orchestrator_command(httpx_client, orchestrator_url: str, command: str, timeout_seconds: int = 10, poll_interval: float = 0.5):
    """
    Common function to send commands to orchestrator via A2A protocol
    
    Args:
        httpx_client: HTTP client instance
        orchestrator_url: URL of the orchestrator
        command: Command to send (e.g., "LIST_AGENTS", "REGISTER_AGENT:url", "UNREGISTER_AGENT:id")
        timeout_seconds: Maximum time to wait for task completion
        poll_interval: Interval between polling attempts
    
    Returns:
        dict: Response data with 'success', 'data', and optional 'error' fields
    """
    try:
        # Create A2A client
        card_resolver = A2ACardResolver(httpx_client, orchestrator_url)
        card = await card_resolver.get_agent_card()
        client = A2AClient(httpx_client, agent_card=card)
        
        # Send command
        message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=command))],
            messageId=str(uuid4()),
        )
        
        payload = MessageSendParams(
            message=message,
            configuration=MessageSendConfiguration(
                acceptedOutputModes=["text"],
            ),
        )
        
        response = await client.send_message(
            SendMessageRequest(
                id=str(uuid4()),
                params=payload,
            )
        )
        
        # Handle response
        if hasattr(response, 'root') and hasattr(response.root, 'result'):
            result = response.root.result
            
            # If it's a task, wait for completion
            if isinstance(result, Task):
                task_id = result.id
                
                # Poll for completion
                max_polls = int(timeout_seconds / poll_interval)
                for _ in range(max_polls):
                    await asyncio.sleep(poll_interval)
                    task_response = await client.get_task(
                        GetTaskRequest(
                            id=str(uuid4()),
                            params=TaskQueryParams(id=task_id),
                        )
                    )
                    
                    if hasattr(task_response, 'root') and hasattr(task_response.root, 'result'):
                        task_data = task_response.root.result
                        if hasattr(task_data, 'status') and hasattr(task_data.status, 'state'):
                            if task_data.status.state == TaskState.completed:
                                # Extract response text from artifacts
                                response_text = ""
                                if hasattr(task_data, 'artifacts') and task_data.artifacts:
                                    for artifact in task_data.artifacts:
                                        if hasattr(artifact, 'parts'):
                                            for part in artifact.parts:
                                                if hasattr(part, 'root') and isinstance(part.root, TextPart):
                                                    response_text = part.root.text
                                                    break
                                
                                return {
                                    "success": True,
                                    "data": response_text,
                                    "task_id": task_id
                                }
                            elif task_data.status.state == TaskState.failed:
                                return {
                                    "success": False,
                                    "error": "Task failed",
                                    "task_id": task_id
                                }
                
                return {
                    "success": False,
                    "error": f"Task timed out after {timeout_seconds} seconds",
                    "task_id": task_id
                }
            
            # If it's a direct message response
            elif isinstance(result, Message):
                response_text = ""
                for part in result.parts:
                    if hasattr(part, 'root') and isinstance(part.root, TextPart):
                        response_text = part.root.text
                        break
                
                return {
                    "success": True,
                    "data": response_text
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unexpected result type: {type(result)}"
                }
        
        return {
            "success": False,
            "error": "No result in response"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def get_agents_from_orchestrator(httpx_client, orchestrator_url: str):
    """Get agent list from orchestrator via API call"""
    try:
        response = await send_orchestrator_command(httpx_client, orchestrator_url, "LIST_AGENTS", timeout_seconds=5)
        
        if response["success"]:
            # Parse the JSON response
            import json
            agent_data = json.loads(response["data"])
            if agent_data.get("type") == "agent_list":
                return agent_data.get("agents", [])
        else:
            print(f"⚠️  Could not get agent list from orchestrator: {response.get('error', 'Unknown error')}")
        
        return []
    except Exception as e:
        print(f"⚠️  Could not get agent list from orchestrator: {e}")
        return []


async def register_agent_with_orchestrator(httpx_client, orchestrator_url: str, agent_url: str):
    """Register an agent with the orchestrator"""
    print(f"🔄 Registering agent {agent_url} with orchestrator {orchestrator_url}")
    
    try:
        print(f"📤 Sending registration request...")
        response = await send_orchestrator_command(
            httpx_client, 
            orchestrator_url, 
            f"REGISTER_AGENT:{agent_url}", 
            timeout_seconds=30,
            poll_interval=1.0
        )
        
        if response["success"]:
            print(f"🎉 Registration completed successfully!")
            print(f"📄 {response['data']}")
        else:
            print(f"❌ Registration failed: {response.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Registration failed: {e}")


async def unregister_agent_with_orchestrator(httpx_client, orchestrator_url: str, agent_identifier: str):
    """Unregister an agent from the orchestrator"""
    print(f"🔄 Unregistering agent {agent_identifier} from orchestrator {orchestrator_url}")
    
    try:
        print(f"📤 Sending unregistration request...")
        response = await send_orchestrator_command(
            httpx_client, 
            orchestrator_url, 
            f"UNREGISTER_AGENT:{agent_identifier}", 
            timeout_seconds=30,
            poll_interval=1.0
        )
        
        if response["success"]:
            print(f"🎉 Unregistration completed successfully!")
            print(f"📄 {response['data']}")
        else:
            print(f"❌ Unregistration failed: {response.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Unregistration failed: {e}")


@click.command()
@click.option("--agent", default="http://localhost:8000")
@click.option("--list_agent", is_flag=True, help="List all available agents from orchestrator")
@click.option("--register_agent", default="")
@click.option("--unregister_agent", default="")
@click.option("--session", default=0)
@click.option("--history", default=False)
@click.option("--use_push_notifications", default=False)
@click.option("--push_notification_receiver", default="http://localhost:5000")
@click.option("--header", multiple=True)
async def orchestratorClient(
    agent,
    list_agent,
    register_agent,
    unregister_agent,
    session,
    history,
    use_push_notifications: bool,
    push_notification_receiver: str,
    header,
):
    headers = {h.split("=")[0]: h.split("=")[1] for h in header}
    print(f"Will use headers: {headers}")
    async with httpx.AsyncClient(timeout=30, headers=headers) as httpx_client:
        card_resolver = A2ACardResolver(httpx_client, agent)
        card = await card_resolver.get_agent_card()

        print("======= Agent Card ========")
        print(card.model_dump_json(exclude_none=True))
        
        # Handle list_agent flag
        if list_agent:
            await list_available_agents(httpx_client, agent, card)
            return
        
        # Handle register_agent option
        if register_agent != "":
            await register_agent_with_orchestrator(httpx_client, agent, register_agent)
            return
        if unregister_agent != "":
            await unregister_agent_with_orchestrator(httpx_client, agent, unregister_agent)
            return

        # Default behavior: show available agents and continue with interactive mode
        await list_available_agents(httpx_client, agent, card)

        notif_receiver_parsed = urllib.parse.urlparse(push_notification_receiver)
        notification_receiver_host = notif_receiver_parsed.hostname or "localhost"
        notification_receiver_port = notif_receiver_parsed.port or 5000

        if use_push_notifications:
            from utils.push_notification_listener import (
                PushNotificationListener,
            )

            notification_receiver_auth = PushNotificationReceiverAuth()
            await notification_receiver_auth.load_jwks(f"{agent}/.well-known/jwks.json")

            push_notification_listener = PushNotificationListener(
                host=notification_receiver_host,
                port=notification_receiver_port,
                notification_receiver_auth=notification_receiver_auth,
            )
            push_notification_listener.start()

        client = A2AClient(httpx_client, agent_card=card)

        continue_loop = True
        streaming = card.capabilities.streaming
        context_id = session if session > 0 else uuid4().hex

        while continue_loop:
            print("=========  starting a new task ======== ")
            continue_loop, _, taskId = await completeTask(
                client,
                streaming,
                use_push_notifications,
                notification_receiver_host,
                notification_receiver_port,
                None,
                context_id,
            )

            if history and continue_loop:
                print("========= history ======== ")
                task_response = await client.get_task(
                    GetTaskRequest(
                        id=str(uuid4()),
                        params=TaskQueryParams(id=taskId or "", historyLength=10),
                    )
                )
                print(
                    task_response.model_dump_json(include={"result": {"history": True}})
                )


async def completeTask(
    client: A2AClient,
    streaming,
    use_push_notifications: bool,
    notification_receiver_host: str,
    notification_receiver_port: int,
    taskId,
    contextId,
):
    prompt = click.prompt(
        "\nWhat do you want to send to the agent? (:q or quit to exit)"
    )
    if prompt == ":q" or prompt == "quit":
        return False, None, None

    message = Message(
        role=Role.user,
        parts=[Part(root=TextPart(text=prompt))],
        messageId=str(uuid4()),
        taskId=taskId,
        contextId=contextId,
    )

    file_path = click.prompt(
        "Select a file path to attach? (press enter to skip)",
        default="",
        show_default=False,
    )
    if file_path and file_path.strip() != "":
        with open(file_path, "rb") as f:
            file_content = base64.b64encode(f.read()).decode("utf-8")
            file_name = os.path.basename(file_path)

        message.parts.append(
            Part(root=FilePart(file=FileWithBytes(name=file_name, bytes=file_content)))
        )

    payload = MessageSendParams(
        message=message,
        configuration=MessageSendConfiguration(
            acceptedOutputModes=["text"],
        ),
    )

    if use_push_notifications:
        # Note: This is a simplified version; proper implementation would need to handle push notifications
        pass

    taskResult = None
    response_message = None
    if streaming:
        response_stream = client.send_message_streaming(
            SendStreamingMessageRequest(
                id=str(uuid4()),
                params=payload,
            )
        )
        async for result in response_stream:
            if isinstance(result.root, JSONRPCErrorResponse):
                print("Error: ", result.root.error)
                return False, contextId, taskId
            event = result.root.result
            contextId = event.contextId
            if isinstance(event, Task):
                taskId = event.id
            elif isinstance(event, TaskStatusUpdateEvent) or isinstance(
                event, TaskArtifactUpdateEvent
            ):
                taskId = event.taskId
            elif isinstance(event, Message):
                response_message = event
            print(f"stream event => {event.model_dump_json(exclude_none=True)}")
        # Upon completion of the stream. Retrieve the full task if one was made.
        if taskId:
            taskResult = await client.get_task(
                GetTaskRequest(
                    id=str(uuid4()),
                    params=TaskQueryParams(id=taskId),
                )
            )
            taskResult = taskResult.root.result
    else:
        try:
            # For non-streaming, assume the response is a task or message.
            event = await client.send_message(
                SendMessageRequest(
                    id=str(uuid4()),
                    params=payload,
                )
            )
            event = event.root.result
        except Exception as e:
            print("Failed to complete the call", e)
        if not contextId:
            contextId = event.contextId
        if isinstance(event, Task):
            if not taskId:
                taskId = event.id
            taskResult = event
        elif isinstance(event, Message):
            response_message = event

    if response_message:
        # Try to format AI response for readability
        message_content = response_message.model_dump_json(exclude_none=True)
        try:
            content_data = json.loads(message_content)
            if not format_ai_response(content_data):
                print(f"\n{message_content}")
        except:
            print(f"\n{message_content}")
        return True, contextId, taskId
    if taskResult:
        # Try to format AI response for readability
        task_content = taskResult.model_dump_json(
            exclude={
                "history": {
                    "__all__": {
                        "parts": {
                            "__all__": {"file"},
                        },
                    },
                },
            },
            exclude_none=True,
        )
        
        try:
            content_data = json.loads(task_content)
            if not format_ai_response(content_data):
                print(f"\n{task_content}")
        except:
            print(f"\n{task_content}")
        
        ## if the result is that more input is required, loop again.
        state = TaskState(taskResult.status.state)
        if state.name == TaskState.input_required.name:
            return (
                await completeTask(
                    client,
                    streaming,
                    use_push_notifications,
                    notification_receiver_host,
                    notification_receiver_port,
                    taskId,
                    contextId,
                ),
                contextId,
                taskId,
            )
        ## task is complete
        return True, contextId, taskId
    ## Failure case, shouldn't reach
    return True, contextId, taskId


if __name__ == "__main__":
    orchestratorClient()
