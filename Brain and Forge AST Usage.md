
### How Brain and Forge Interact with Stubs

Even though we are keeping the microservices decoupled by copying the `ast_parser.py` file into both repos, they will use the stubs in two distinct ways:

1. **Brain OS (On-Demand Recon):** We will give Brain OS a new tool called `read_file_signatures`. When the Architect agent is asked "How does the payment system work?", it won't blind-read the massive `payments.py` file. It will use the stubbing tool first to cheaply map out the available classes and functions, and _then_ use `read_safe_file` to zoom in on the exact function it needs.
    
2. **Forge (Automated Context Injection):** Forge's `orchestrator.py` will use stubbing automatically. During the `assemble_context` phase, Forge will generate an AST stub for _every single file_ in the repository and inject it into the prompt cache. This gives the Engineering agent a god-like omnipresence of the entire codebase for mere pennies.


### How Brain and Forge Actually Use ASTs

To understand how this drastically changes the architecture, you have to picture what the AI "sees" versus what the compiler "knows."

Currently, if the AI needs to modify a `User` class, it has to read the entire `models.py` file. If `models.py` is 2,000 lines long, it burns thousands of tokens just to find out that `def get_user_by_id(id: int)` exists.

By using an AST, we parse the code into a mathematical tree. We write a query that searches the tree for `function_definition` nodes, captures the `name` and `parameters`, and actively _deletes_ the `block` node (the actual code inside the function). This is called "stubbing."

Here is how both systems will use these stubs:

#### 1. Brain OS: The "Scout" Tool (On-Demand)

In Brain OS, we give the Architect agent a new tool: `read_file_signatures`.

- **The Scenario:** You ask Brain OS, "Can you review the security of the payment pipeline in my Forge repo?"
    
- **The Scout:** The Architect doesn't know where the payment logic is. Instead of blindly reading whole files, it uses `read_file_signatures("src/payments.py")`.
    
- **The Return:** Brain OS runs the AST extractor and returns a tiny, 20-line summary of all the classes and functions inside that file.
    
- **The Strike:** Now that the Architect knows exactly what the functions are called and what arguments they take, it uses the standard `read_safe_file` tool to zoom in and read only the specific function body it needs to audit.
    

#### 2. Forge: The "Omniscience" Loop (Automated)

Forge's `orchestrator.py` works differently. It doesn't rely on the AI manually calling tools to read files; it aggressively injects context via the `assemble_context` function.

- **The Scenario:** You ask Forge to "Add a 'Refund' button to the dashboard."
    
- **The Funnel:** Before the Engineering agent wakes up, Forge's Python orchestrator iterates through your entire repository.
    
- **The Stubbing:** It runs every `.py` and `.tsx` file through the Tree-Sitter AST extractor, generating stubs for the entire codebase.
    
- **The Prompt:** It wraps these stubs in our new XML caching tags (`<document path="src/api/refunds.py"> ... stubs ... </document>`) and sends it to the AI.
    

**The Result:** When the Claude 3.5 Sonnet agent wakes up in Forge, it literally has god-like, omniscient awareness of every single function, class, and React Prop interface in your entire codebase without having to search for them, all while only consuming about 5% of the typical token cost.

If your test is green, the next step is writing the LISP-style Tree-Sitter query to actually chop the bodies out of the Python functions. Are you ready to write the extraction query?