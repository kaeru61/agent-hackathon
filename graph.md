```mermaid
%%{init: {'flowchart': {'curve': 'linear'}}}%%
graph TD;
	__start__([<p>__start__</p>]):::first
	select_role(select_role)
	select_task(select_task)
	execute_task(execute_task)
	end(end)
	__end__([<p>__end__</p>]):::last
	__start__ --> select_role;
	end --> __end__;
	execute_task --> end;
	select_role --> select_task;
	select_task --> execute_task;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
```