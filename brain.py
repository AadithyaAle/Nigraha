import boto3
import json
from rich.console import Console

console = Console()

def ask_nova(system_context, user_problem, learning_mode=False, user_profile=None):
    """
    Connects to Amazon Nova via AWS Bedrock.
    Falls back to a safe mock response if the network drops.
    """
    try:
        # 1. Explicitly load your exact SSO profile
        session = boto3.Session(profile_name="Stack-Sentinel")
        
        # 2. Force the region to us-east-1 where Nova is hosted
        client = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # 1. Build the System Prompt (Context)
        system_prompt = f"You are StackSentinel, an AI Linux Repair Agent. System Context: {json.dumps(system_context)}"
        if user_profile:
            system_prompt += f" User Profile: {user_profile}"
            
        system_instruction = [{"text": system_prompt}]

        # 2. Build the User Message
        user_message = f"""
        [THE ERROR]
        {user_problem}
        
        [INSTRUCTIONS]
        1. Analyze the error.
        2. Provide a BRIEF explanation.
        3. Provide a BASH COMMAND to fix it inside a ```bash block.
        4. If risky, provide a backup command inside a **Backup Command:** ```bash block.
        """
        
        messages = [
            {"role": "user", "content": [{"text": user_message}]}
        ]

        # 3. Invoke the Converse API
        # Using Nova Lite for the best balance of speed and reasoning
        response = client.converse(
            modelId="amazon.nova-2-lite-v1:0", 
            messages=messages,
            system=system_instruction,
            inferenceConfig={
                "temperature": 0.5,
                "maxTokens": 512
            }
        )
        
        # Extract the text from the response
        return response['output']['message']['content'][0]['text']

    except Exception as e:
        console.print(f"[dim red]⚠️ AI Connection Failed: {e}. Using Offline Mode.[/dim red]")
        return _mock_fallback(user_problem)

def _mock_fallback(problem):
    """Failsafe so your demo never crashes without internet."""
    problem_lower = problem.lower()
    if "wifi" in problem_lower:
        return "Offline Diagnosis: WiFi interface down.\n\nFix:\n```bash\nsudo nmcli radio wifi on\n```"
    return "Offline Diagnosis: Generic error.\n\nFix:\n```bash\necho 'System Diagnostic Complete'\n```"

def audit_command(command):
    """The Safety Layer"""
    dangerous = ["rm -rf /*", "mkfs", ":(){ :|:& };:", "dd if=/dev/zero"]
    for danger in dangerous:
        if danger in command:
            return f"BLOCKED: Dangerous command detected ({danger})"
    return "SAFE"