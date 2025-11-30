import asyncio
import argparse
import json
from app.services.smard import SmardClient
from app.services.elexon import ElexonClient
from app.agent import EnergyAgent

async def main():
    parser = argparse.ArgumentParser(description="Energy Trading Insight Agent CLI")
    parser.add_argument("--source", choices=["smard", "elexon"], required=True, help="Data source to analyze")
    parser.add_argument("--output", help="File to save the insight JSON to")
    args = parser.parse_args()

    print(f"🚀 Starting Energy Trading Insight Agent (Source: {args.source})...")

    agent = EnergyAgent()
    
    try:
        if args.source == "smard":
            client = SmardClient()
            print("📊 Fetching data from SMARD...")
            market_data = await client.get_wholesale_prices()
        elif args.source == "elexon":
            client = ElexonClient()
            print("📊 Fetching data from Elexon...")
            market_data = await client.get_system_prices()
        
        print("fw Analyzing data with AI Agent...")
        insight = await agent.analyze(market_data)
        
        # Print result to console
        print("\n" + "="*50)
        print(f"📈 INSIGHT REPORT ({args.source.upper()})")
        print("="*50)
        print(f"Action: {insight.action}")
        print(f"Confidence: {insight.confidence}")
        print(f"Summary: {insight.summary}")
        print("Reasoning:")
        for reason in insight.reasoning:
            print(f" - {reason}")
        print("="*50 + "\n")

        if args.output:
            with open(args.output, "w") as f:
                f.write(insight.model_dump_json(indent=2))
            print(f"✅ Insight saved to {args.output}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
