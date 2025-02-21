```mermaid
%%{init: {'flowchart': {'curve': 'linear'}}}%%
graph TD;
	__start__([<p>__start__</p>]):::first
	generate_message(generate_message)
	end(end)
	__end__([<p>__end__</p>]):::last
	__start__ --> generate_message;
	end --> __end__;
	generate_message --> end;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
```