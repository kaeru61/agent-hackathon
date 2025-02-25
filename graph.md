```mermaid
%%{init: {'flowchart': {'curve': 'linear'}}}%%
graph TD;
	__start__([<p>__start__</p>]):::first
	judge_question(judge_question)
	select_role(select_role)
	select_task(select_task)
	execute_task(execute_task)
	generate_message(generate_message)
	end(end)
	__end__(<p>__end__</p>)
	__start__ --> judge_question;
	end --> __end__;
	execute_task --> end;
	select_role --> select_task;
	select_task --> execute_task;
	judge_question -. &nbsp;False&nbsp; .-> select_role;
	judge_question -. &nbsp;True&nbsp; .-> generate_message;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
```