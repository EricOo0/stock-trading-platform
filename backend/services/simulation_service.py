import os
import json
import logging
import requests
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'simulations.json')

class SimulationService:
    def __init__(self):
        self.agent_api_url = "http://localhost:9000/chat"
        self._ensure_data_dir()
        self.tasks = self._load_data()

    def _ensure_data_dir(self):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'w') as f:
                json.dump({}, f)

    def _load_data(self) -> Dict[str, Any]:
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load simulation data: {e}")
            return {}

    def _save_data(self):
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self.tasks, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save simulation data: {e}")

    def get_all_tasks(self) -> List[Dict]:
        return list(self.tasks.values())
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        return self.tasks.get(task_id)

    def create_task(self, symbol: str, initial_capital: float = 10000.0) -> Dict:
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "symbol": symbol.upper(),
            "created_at": datetime.now().isoformat(),
            "initial_capital": initial_capital,
            "current_cash": initial_capital,
            "holdings": 0,  # Number of shares
            "total_value": initial_capital,
            "transactions": [],
            "daily_records": [],
            "status": "active" 
        }
        self.tasks[task_id] = task
        self._save_data()
        return task
    
    def delete_task(self, task_id: str) -> bool:
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_data()
            return True
        return False

    
    def _gather_market_state(self, symbol: str, tools_instance) -> Dict[str, Any]:
        """
        Aggregate all market data for the decision engine.
        Dimensions: Technical, Fundamental, Macro, Sentiment
        """
        state = {}
        
        # 1. Technical Analysis (Logic handled by new TechnicalAnalysisTool via Registry)
        try:
            logger.info(f"Gathering Technicals for {symbol}")
            # Get 60 days history for MA60
            indicators = tools_instance.get_technical_indicators(symbol, period="60d")
            state['technical'] = indicators
            # Extract current price from technicals or fetch specifically
            # We need a fallback price if technicals fail
        except Exception as e:
            logger.error(f"Technical gathering failed: {e}")
            state['technical'] = {"error": str(e)}

        # 2. Fundamentals (Valuation & Growth)
        try:
            logger.info(f"Gathering Fundamentals for {symbol}")
            fin_data = tools_instance.get_financial_indicators(symbol)
            state['fundamental'] = {
                "valuation": fin_data.get('valuation', {}),
                "growth": fin_data.get('revenue', {}),
                "profitability": fin_data.get('profit', {}),
                "debt": fin_data.get('debt', {})
            }
        except Exception as e:
            logger.error(f"Fundamental gathering failed: {e}")
            state['fundamental'] = {"error": str(e)}

        # 3. Macro Environment
        try:
            logger.info(f"Gathering Macro Data")
            # Parallel fetch could be better, sequential for now
            vix = tools_instance.get_macro_data("VIX")
            us10y = tools_instance.get_macro_data("US10Y")
            state['macro'] = {
                "vix": vix.get('value', 0) if 'value' in vix else None,
                "us10y": us10y.get('value', 0) if 'value' in us10y else None
            }
        except Exception as e:
            logger.error(f"Macro gathering failed: {e}")
            state['macro'] = {}

        # 4. News & Sentiment
        try:
            logger.info(f"Gathering News & Sentiment for {symbol}")
            news = tools_instance.search_market_news(f"{symbol} stock news")
            # Analyze top 5
            top_news = news[:5] if news else []
            sentiment = tools_instance.analyze_sentiment(top_news)
            state['sentiment'] = {
                "score": sentiment.get('average_score', 0),
                "label": sentiment.get('overall_sentiment', 'NEUTRAL'),
                "news_summary": [n.get('title') for n in top_news]
            }
        except Exception as e:
            logger.error(f"Sentiment gathering failed: {e}")
            state['sentiment'] = {}
            
        return state

    def run_daily_simulation(self, task_id: str, tools_instance) -> Dict:
        """
        Run a single day simulation step with Multi-Factor Decision Model.
        """
        task = self.tasks.get(task_id)
        if not task: raise ValueError("Task not found")
        symbol = task['symbol']
        
        # --- Step 1: Aggregate Data ---
        market_state = self._gather_market_state(symbol, tools_instance)
        
        # Get Real-time Price (Critical for execution)
        price_data = tools_instance.get_stock_price(symbol)
        current_price = price_data.get('current_price')
        if not current_price: raise ValueError("Failed to get current price")
        
        current_date_str = datetime.now().strftime('%Y-%m-%d')
        
        # --- Step 2: Construct Rigorous Prompt ---
        portfolio_ctx = (
            f"Cash: ${task['current_cash']:.2f}\n"
            f"Holdings: {task['holdings']} shares\n"
            f"Total NAV: ${(task['current_cash'] + task['holdings'] * current_price):.2f}\n"
            f"Current Price: ${current_price}"
        )
        
        tech_ctx = json.dumps(market_state.get('technical', {}), indent=2)
        fund_ctx = json.dumps(market_state.get('fundamental', {}), indent=2)
        macro_ctx = json.dumps(market_state.get('macro', {}), indent=2)
        sent_ctx = json.dumps(market_state.get('sentiment', {}), indent=2)
        
        system_persona = (
            "You are a disciplined AI Fund Manager. Your goal is to maximize Alpha while controlling risk.\n"
            "You make decisions based on a Multi-Factor Model: Technical, Fundamental, Macro, and Sentiment.\n"
        )
        
        prompt = (
            f"{system_persona}\n"
            f"### 1. Portfolio Status\n{portfolio_ctx}\n\n"
            f"### 2. Market Data Analysis\n"
            f"- **Technical Indicators** (Trend/Momentum): \n{tech_ctx}\n"
            f"- **Fundamentals** (Valuation/Growth): \n{fund_ctx}\n"
            f"- **Macro Environment** (Risk Context): \n{macro_ctx}\n"
            f"- **News & Sentiment**: \n{sent_ctx}\n\n"
            f"### 3. Decision Required\n"
            f"Analyze the data step-by-step. Rate each factor (0-10) then make a final decision.\n"
            f"Constraints:\n"
            f"- Max trade size: 20% of NAV.\n"
            f"- If Trend is DOWN and Sentiment is NEGATIVE, bias towards SELL or HOLD.\n"
            f"- If Valuation is LOW and Trend is UP, bias towards BUY.\n\n"
            f"**Output Format (JSON only):**\n"
            f"{{\n"
            f"  \"analysis\": {{\n"
            f"    \"technical_score\": 0-10,\n"
            f"    \"fundamental_score\": 0-10,\n"
            f"    \"sentiment_score\": 0-10,\n"
            f"    \"macro_score\": 0-10,\n"
            f"    \"reasoning\": \"brief summary of analysis\"\n"
            f"  }},\n"
            f"  \"decision\": {{\n"
            f"    \"action\": \"BUY\" | \"SELL\" | \"HOLD\",\n"
            f"    \"quantity\": <int>,\n"
            f"    \"reason\": \"final execution reason\"\n"
            f"  }}\n"
            f"}}"
        )

        logger.info(f"Asking Agent for decision with Multi-Factor Prompt")
        
        action = "HOLD"
        quantity = 0
        reason = "Agent Error"
        result_json = None # Initialize to avoid UnboundLocalError
        
        try:
            # Call Agent API 
            response = requests.post(
                self.agent_api_url,
                json={"query": prompt, "session_id": f"sim_{task_id}"},
                stream=True, # Enable streaming
                timeout=300
            )
            
            # Handle NDJSON streaming response
            agent_text = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if data.get('type') == 'chunk':
                             agent_text += data.get('content', '')
                    except:
                        pass
            
            logger.info(f"Agent raw response: {agent_text[:200]}...")
            
            # Parse JSON
            import re
            json_match = re.search(r'\{.*\}', agent_text, re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group(0))
                # Support both nested structure and flat structure if agent hallucinates
                decision = result_json.get('decision', result_json) 
                
                action = decision.get('action', 'HOLD').upper()
                quantity = int(decision.get('quantity', 0))
                reason = decision.get('reason', 'Agent decided')
                
                # Extract analysis for logging if available
                analysis = result_json.get('analysis', {})
                if analysis:
                    reason = f"[{analysis.get('technical_score',0)}/{analysis.get('fundamental_score',0)}] {reason}"
            else:
                logger.warning("Could not parse JSON from agent")
                reason = "Failed to parse Agent output"

        except Exception as e:
            logger.error(f"Agent call failed: {e}")
            reason = f"System Error: {str(e)}"

        # --- Step 4: Execute & Record (Same as before) ---

        # 4. Execute Logic
        executed_price = current_price
        transaction = None
        
        if action == 'BUY':
            cost = quantity * executed_price
            if cost > 0 and cost <= task['current_cash']:
                task['current_cash'] -= cost
                task['holdings'] += quantity
                transaction = {
                    "date": current_date_str,
                    "action": "BUY",
                    "price": executed_price,
                    "quantity": quantity,
                    "amount": cost,
                    "reason": reason
                }
            else:
                reason += " (Insufficient funds or 0 quantity)"
                action = "HOLD" # Fallback

        elif action == 'SELL':
            if quantity > 0 and quantity <= task['holdings']:
                revenue = quantity * executed_price
                task['current_cash'] += revenue
                task['holdings'] -= quantity
                transaction = {
                    "date": current_date_str,
                    "action": "SELL",
                    "price": executed_price,
                    "quantity": quantity,
                    "amount": revenue,
                    "reason": reason
                }
            else:
                reason += " (Insufficient holdings or 0 quantity)"
                action = "HOLD"

        if transaction:
            task['transactions'].append(transaction)

        # Update Daily Record
        stock_value = task['holdings'] * current_price
        task['total_value'] = task['current_cash'] + stock_value
        
        record = {
            "date": current_date_str,
            "price": executed_price,
            "holdings": task['holdings'],
            "cash": task['current_cash'],
            "stock_value": stock_value, # Explicitly separate stock value
            "total_value": task['total_value'],
            "action_taken": action,
            "quantity": quantity,
            "reason": reason,
            "analysis": result_json.get('analysis') if result_json else None
        }

        # Check if we already have a record for today
        if task['daily_records'] and task['daily_records'][-1]['date'] == current_date_str:
            # Update existing record for today (Aggregate for chart/log view)
            task['daily_records'][-1] = record
        else:
            # Append new day
            task['daily_records'].append(record)
        
        self._save_data()
        
        return {
            "status": "success",
            "action": action,
            "transaction": transaction,
            "daily_record": record
        }

