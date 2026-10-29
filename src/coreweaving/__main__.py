"""Terminal entrypoint; UI and evaluations use the same Agent.run implementation."""

import argparse
import json

from coreweaving.agent import Agent, Session
from coreweaving.config import init_weave, settings
from coreweaving.corpus import Corpus


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="?")
    parser.add_argument("--json", action="store_true", help="Print the answer, sources and checks as JSON.")
    args = parser.parse_args()
    client = init_weave()
    agent, session = Agent(Corpus(), settings()), Session()
    while True:
        question = args.question or input("You (blank to quit): ").strip()
        if not question:
            break
        result = agent.run(question, session)
        print(json.dumps(result, indent=2) if args.json else result["answer"])
        if not args.json:
            print(f"\nView the steps behind this answer in Weave: {result['trace_url']}\n")
        client.flush()
        if args.question:
            break


if __name__ == "__main__":
    main()
