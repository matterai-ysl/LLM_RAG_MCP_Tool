#!/usr/bin/env python3
"""
Materials Science MCP Server (English Version)
Specialized Q&A system for materials science questions with OpenScholar RAG and LLM fallback
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
import json
import argparse
from fastmcp import FastMCP
from playwright.async_api import async_playwright
from litellm import acompletion
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MCP server instance
mcp = FastMCP("Materials Science RAG Server")

# Global configuration
MAX_RETRIES = 3
TIMEOUT_SECONDS = 180
CONCURRENT_LIMIT = 5  # Limit concurrent sessions
active_sessions = asyncio.Semaphore(CONCURRENT_LIMIT)

class OpenScholarScraper:
    """OpenScholar web scraper"""
    
    def __init__(self):
        self.browser = None
        self.context = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        try:
            playwright = await async_playwright().__aenter__()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-extensions'
                ]
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            return self
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
    
    async def search_materials_science(self, question: str) -> Dict[str, Any]:
        """Search materials science questions on OpenScholar"""
        page = None
        try:
            page = await self.context.new_page()
            
            # Navigate to OpenScholar
            logger.info(f"Navigating to OpenScholar for question: {question[:50]}...")
            await page.goto('https://openscholar.allen.ai', wait_until='networkidle', timeout=30000)
            
            # Input question
            input_box = page.locator('textarea[data-testid="message-bar-input"]')
            await input_box.fill(question)
            
            # Submit question
            submit_button = page.locator('button[data-testid="message-bar-submit-button"]')
            await submit_button.wait_for(state="attached", timeout=10000)
            await submit_button.click(force=True)
            
            # Handle possible confirmation dialog
            try:
                use_queries_button = page.locator('button', has_text="Ok to use my queries")
                await use_queries_button.wait_for(timeout=5000)
                await use_queries_button.click(force=True)
            except:
                pass  # Continue if button doesn't exist
            
            # Submit again
            await page.get_by_test_id("message-bar-submit-button").click()
            
            # Wait for answer to load
            await page.wait_for_selector(
                'p.MuiTypography-root.MuiTypography-body1.MuiTypography-paragraph.css-z94edi', 
                timeout=TIMEOUT_SECONDS * 1000
            )
            
            # Additional wait to ensure content is fully loaded
            await page.wait_for_timeout(3000)
            
            # Extract answer content
            feedback_texts = await page.locator(
                'p.MuiTypography-root.MuiTypography-body1.MuiTypography-paragraph.css-z94edi'
            ).all_text_contents()
            
            # Extract references
            references = []
            references_section = page.locator('h3#references').first
            if await references_section.count() > 0:
                references_list = page.locator('h3#references + ul li')
                reference_items = await references_list.all()
                
                for item in reference_items:
                    ref_text = await item.text_content()
                    ref_text = ' '.join(ref_text.split())
                    if ref_text.strip():
                        references.append(ref_text.strip())
            
            # Combine answer
            answer_text = ''.join(feedback_texts)
            
            result = {
                'success': True,
                'answer': answer_text,
                'references': references,
                'source': 'OpenScholar',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully retrieved answer with {len(references)} references")
            return result
            
        except Exception as e:
            logger.error(f"Error during web scraping: {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'OpenScholar',
                'timestamp': datetime.now().isoformat()
            }
        
        finally:
            if page:
                await page.close()

async def get_llm_answer(question: str) -> Dict[str, Any]:
    """Get general answer using LiteLLM"""
    try:
        logger.info("Getting general answer from LLM...")
        
        # Construct focused prompt for materials science
        prompt = f"""As a materials science expert, provide a focused, accurate answer to this specific question:

{question}

Requirements:
- Focus ONLY on answering the specific question asked
- Provide scientific facts and established knowledge
- Include relevant technical details and mechanisms
- Do NOT fabricate or invent citations/references
- Keep the response comprehensive but directly relevant
- Use clear, technical language appropriate for the field

Answer only what you know with confidence. Do not create fictional references."""

        response = await acompletion(
            model="openai/gpt-5",
            messages=[{"role": "user", "content": prompt}],
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("BASE_URL"),
            timeout=60
        )
        
        answer = response.choices[0].message.content # type: ignore
        
        return {
            'success': True,
            'answer': answer,
            'source': 'LiteLLM (GPT-4o)',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"LLM failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'source': 'LiteLLM',
            'timestamp': datetime.now().isoformat()
        }

@mcp.tool()
async def answer_materials_science_question(question: str) -> str:
    """
    Answer materials science questions using RAG retrieval and LLM fallback.
    
    CRITICAL INSTRUCTIONS FOR AI AGENT:
    
    INPUT REQUIREMENTS:
    - This tool ONLY accepts ENGLISH input
    - NO conversation history is maintained between requests
    - Input should be precise, well-formulated questions
    - EXTRACT and REFINE user questions from conversation history before calling this tool
    - DO NOT directly forward vague user queries - refine them first
    
    OUTPUT PROCESSING:
    - Tool returns JSON with BOTH RAG and LLM answers
    - AI agent should SYNTHESIZE both answers into a comprehensive response
    - PRIORITIZE RAG answer when available (academic literature)
    - Use LLM answer to fill gaps or when RAG fails
    - INCLUDE proper citations from the references array in RAG results
    - FORMAT citations properly in the final response to user
    - Do not fabricate references; only select references from those returned by RAG.
    
    RESPONSE SYNTHESIS GUIDELINES:
    1. If RAG successful: Use as primary source + add LLM insights + format references
    2. If RAG failed: Use LLM answer but indicate it's general AI knowledge
    3. Always cite sources appropriately in your response to user
    4. Combine complementary information from both sources
    5. Do not fabricate references; only select references from those returned by RAG.
    
    Args:
        question: Precisely formulated materials science question in English
    
    Returns:
        JSON string with rag_retrieval and llm_answer objects for synthesis
    """
    
    # Limit concurrent sessions
    async with active_sessions:
        logger.info(f"Processing question: {question[:100]}...")
        
        # Initialize results
        rag_result = None
        llm_result = None
        
        # Try RAG approach with retries
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"RAG attempt {attempt + 1}/{MAX_RETRIES}")
                async with OpenScholarScraper() as scraper:
                    rag_result = await scraper.search_materials_science(question)
                    if rag_result['success']:
                        break
                    else:
                        logger.warning(f"RAG attempt {attempt + 1} failed: {rag_result.get('error', 'Unknown error')}")
                        
            except Exception as e:
                logger.error(f"RAG attempt {attempt + 1} exception: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # Always get LLM answer as well
        try:
            llm_result = await get_llm_answer(question)
        except Exception as e:
            logger.error(f"LLM answer failed: {e}")
            llm_result = {
                'success': False,
                'error': str(e),
                'source': 'LiteLLM',
                'timestamp': datetime.now().isoformat()
            }
        
        # Prepare response JSON
        response_data = {
            'question': question,
            'rag_retrieval': rag_result,
            'llm_answer': llm_result,
            # 'processing_info': {
            #     'concurrent_sessions_used': CONCURRENT_LIMIT - active_sessions._value,
            #     'max_concurrent_limit': CONCURRENT_LIMIT,
            #     'max_retries': MAX_RETRIES,
            #     'timeout_seconds': TIMEOUT_SECONDS,
            #     'timestamp': datetime.now().isoformat()
            # }
        }
        print(response_data)
        logger.info("Question processing completed")
        return json.dumps(response_data, indent=2, ensure_ascii=False)

@mcp.tool()
async def get_system_status() -> str:
    """
    Get system status information
    
    Returns:
        JSON string with system status report
    """
    try:
        # Test OpenScholar connection
        test_question = "What is lithium?"
        async with OpenScholarScraper() as scraper:
            test_result = await asyncio.wait_for(
                scraper.search_materials_science(test_question), 
                timeout=30
            )
            openscholar_status = "online" if test_result['success'] else "error"
            openscholar_error = test_result.get('error', None) if not test_result['success'] else None
    except Exception as e:
        openscholar_status = "offline"
        openscholar_error = str(e)
    
    # Test LiteLLM connection
    try:
        test_result = await get_llm_answer("Test question")
        litellm_status = "online" if test_result['success'] else "error"
        litellm_error = test_result.get('error', None) if not test_result['success'] else None
    except Exception as e:
        litellm_status = "offline"
        litellm_error = str(e)
    
    status_data = {
        'system_name': 'Materials Science MCP Server',
        'services': {
            'openscholar_rag': {
                'status': openscholar_status,
                'error': openscholar_error,
                'description': 'Academic literature retrieval from OpenScholar'
            },
            'litellm_fallback': {
                'status': litellm_status, 
                'error': litellm_error,
                'description': 'General AI answer using LiteLLM'
            }
        },
        'configuration': {
            'max_concurrent_sessions': CONCURRENT_LIMIT,
            'current_active_sessions': CONCURRENT_LIMIT - active_sessions._value,
            'timeout_seconds': TIMEOUT_SECONDS,
            'max_retries': MAX_RETRIES
        },
        'capabilities': [
            'Materials science question answering',
            'Academic literature retrieval',
            'Reference extraction and formatting',
            'Concurrent request handling',
            'Automatic retry mechanism',
            'Dual-source answers (RAG + LLM)'
        ],
        'limitations': [
            'English input only',
            'No conversation history',
            'Requires precise question formulation',
            'Subject to OpenScholar availability'
        ],
        'timestamp': datetime.now().isoformat()
    }
    
    return json.dumps(status_data, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Materials Science RAG MCP Server")
    parser.add_argument('transport', nargs='?', default='streamable-http', choices=['stdio', 'sse', 'streamable-http'],
                        help='Transport type (stdio, sse, or streamable-http)')
    args = parser.parse_args()
    
    # Run the MCP server with the specified transport
    mcp.run(transport=args.transport,port=8110)