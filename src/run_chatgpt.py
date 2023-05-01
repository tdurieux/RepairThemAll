#!/usr/bin/env python
# -*- encoding: utf-8 -*-


'''
@Author  :   Sen Fang
@Email   :   senf@kth.se
@Ide     :   vscode & conda
@File    :   run_chatgpt.py
@Time    :   2023/04/01 11:52:36
'''

"""This code is derived from ask_defects4j.py and can request ChatGPT or its improved version for program repair."""

import argparse
import time
import os
import json
from core.chatgpt.config.defs4j_config import AttrDict
from core.chatgpt.config.prompt_config import PROMPT
from core.chatgpt.ask_chatgpt_for_pr import ask_chatgpt_for_defect4j, ask_chatgpt_for_refactory
from core.tools.load_paths import load_paths


def main():
    parser = argparse.ArgumentParser(
        prog="ask", description='Checkout and fix the bug by chatable large language model')
    parser.add_argument("--model", "-m", required=True, choices=["gpt-3.5-turbo", "gpt-4", "gpt-4-32k"],
                        help="The chatable LLMs you want to use.")
    parser.add_argument("--only_request", "-or", type=bool, default=False, help="Only request the chatget to generate patch.")
    parser.add_argument("--only_verify", "-ov", type=bool, default=False, help="Only verify the patch generated by chatget.")
    parser.add_argument("--benchmark", "-b", required=True, default="Defects4J",
                        help="The benchmark to repair.")
    parser.add_argument("--project", "-p", required=False,
                        help="The project name (case sensitive).")
    parser.add_argument("--bug_id", "-bi", required=False, help="The bug id")
    parser.add_argument("--start", "-s", required=False,
                        help="The bug id starts from")
    parser.add_argument("--working_directory", "-w",
                        required=True, help="The working directory")
    parser.add_argument("--num_samples", "-ns", type=int, default=10, help="The number of samples to generate.")
    parser.add_argument("--num_requests", "-nr", type=int, default=10, help="The number of requests to generate.")
    parser.add_argument("--temperature", "-t", type=float, default=0.8, help="The temperature used to generate the patch.")
    parser.add_argument("--max_tokens", "-mt", type=int, default=3000, help="The max tokens used to generate the patch.")
    parser.add_argument("--top_p", "-tp", type=float, default=1., help="The top_p used to generate the patch.")
    parser.add_argument("--question_id", "-qi", type=int, default=1, choices=[1, 2, 3, 4, 5], help="The question id used to generate the patch for refactory benchmark.")
    parser.add_argument("--presence_penalty", "-pp", type=float, default=0.0, help="The presence_penalty used to generate the patch.")
    parser.add_argument("--frequency_penalty", "-fp", type=float, default=0.0, help="The frequency_penalty used to generate the patch.")
    parser.add_argument("--prompt_level", "-pml", type=str, default="easy", choices=["easy", "advanced", "domain"], help="The prompt used to generate the patch.")
    parser.add_argument("--prompt", "-pm", type=str, default=None, help="The prompt used to generate the patch.")
    parser.add_argument("--pl", "-pl", type=str, default="java", help="The programming language want to fix.")

    args = parser.parse_args()
    if args.benchmark == "Defects4J":
        defects4j_config = AttrDict()
        fixa_config = defects4j_config.fixa_config
        defects4j_projects = defects4j_config.defects4j_projects
        defects4j_bug_size = defects4j_config.defects4j_bug_size
        defects4j_config.benchmark = args.benchmark
        if args.project != None:
            defects4j_config.project = args.project
        if args.bug_id != None:
            defects4j_config.bug_id = args.bug_id
        defects4j_config.model = args.model
        args.working_directory = args.model + "_" + args.working_directory + "_" + args.prompt_level
        assert args.project in defects4j_projects or args.project == None, "The project name is not valid, please check!"
        
        if args.prompt == None:
            args.prompt = PROMPT[args.prompt_level].replace("{}", args.pl)
        
        fixa_config['sample'] = args.num_samples

        if args.project != None and args.bug_id != None:
            print("Fixing bug: ", args.project, args.bug_id, "...")
            ask_chatgpt_for_defect4j(args, defects4j_config, fixa_config)
        elif args.project != None and args.bug_id == None:
            # fix all bugs in a project
            print("Fixing all bugs in project: ", args.project, "...")
            bug_size = defects4j_bug_size[args.project]
            starts_from = int(args.start) if args.start != None else 1
            for bug_id in range(starts_from, bug_size + 1):
                defects4j_config.bug_id = bug_id
                args.bug_id = bug_id
                ask_chatgpt_for_defect4j(args, defects4j_config, fixa_config)
        else:
            # fix all bugs from all projects
            print("Fixing all bugs from all projects...")
            for project, bug_size in defects4j_bug_size.items():
                args.project = project
                defects4j_config.project = project
                for bug_id in range(1, bug_size + 1):
                    args.bug_id = bug_id
                    defects4j_config.bug_id = args.bug_id
                    ask_chatgpt_for_defect4j(args, defects4j_config, fixa_config)
    elif args.benchmark == "refactory":
        if args.prompt == None:
            args.prompt = PROMPT[args.prompt_level].replace("{}", args.pl)
        refactory_config = {}
        args.working_directory = "data" + "/benchmarks" + "/" + args.benchmark + "/" + "data" + "/" + "question_{}".format(args.question_id) + "/" + "code" + "/" + "question_{}.json".format(args.question_id)
        benchmark_path = "data" + "/benchmarks" + "/" + args.benchmark + "/" + "data" + "/" + "question_{}".format(args.question_id) + "/" + "code" + "/" + "wrong"
        buggy_code_path = load_paths(benchmark_path)
        # breakpoint()
        for idx, path in enumerate(buggy_code_path):
            # resylts_list: prompt, prompt_size, bug_size, response, patch
            results_list = []
            results_list = ask_chatgpt_for_refactory(args, results_list, path)
            refactory_config[path.split("/")[-1]] = results_list

            if idx * args.num_samples % 20 == 0:
                time.sleep(30)
        with open(args.working_directory, "w") as f:
            json.dump(refactory_config, f, indent=4)


if __name__ == "__main__":
    main()
 