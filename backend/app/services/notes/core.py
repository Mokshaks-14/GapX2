"""Beginner-friendly explanations and extra interview Q&A: programming, DSA, CS core, interview prep."""

NOTES = {
    "JavaScript Core: Scope, Closures & `this`": {
        "simple": [
            ("Scope", "Scope is simply 'where a variable can be seen'. A variable made inside a function is like a note kept in your own room: code outside the room can't read it."),
            ("let, const and var", "Use const for values you won't reassign and let for ones you will. var is the old way: it ignores curly-brace blocks and causes surprises, so avoid it."),
            ("Hoisting", "JavaScript reads your declarations before running the code, as if moving them to the top. With var you get 'undefined' if you use it early; with let/const you get an error, which is safer."),
            ("Closures", "A closure is a function that remembers the variables around it even after the outer function has finished. Like a backpack: the function carries its variables wherever it goes."),
            ("`this`", "`this` means 'the object that called me'. Call obj.greet() and `this` is obj. Arrow functions don't get their own `this`; they borrow it from where they were written."),
        ],
        "qa": [
            ("What is the difference between == and ===?", "== converts types before comparing, so 0 == '0' is true. === compares value and type, so 0 === '0' is false. Use === to avoid surprises."),
            ("Why does a setTimeout inside a var loop print the same number?", "var has one shared variable for the whole loop, so every callback sees its final value. let creates a fresh variable each iteration, fixing it."),
            ("When would you use bind?", "When passing a method somewhere else (like an event handler) and you need `this` to stay the original object. bind returns a copy of the function with `this` locked."),
        ],
    },
    "Async JavaScript & the Event Loop": {
        "simple": [
            ("Single-threaded", "JavaScript does one thing at a time, like a single cashier. To avoid blocking the queue, slow jobs (network, timers) are handed off and finished later."),
            ("Call stack", "The call stack is the list of functions currently running. A function is added when it starts and removed when it returns."),
            ("Callbacks and Promises", "A Promise is an IOU: 'I'll give you the result later'. You attach .then() for success and .catch() for errors, instead of nesting callbacks."),
            ("async/await", "async/await lets you write Promise code that reads top to bottom like normal code. await pauses only that function until the Promise settles; the rest of the app keeps running."),
            ("Microtasks vs macrotasks", "After each piece of code finishes, JavaScript first runs all Promise callbacks (microtasks), then one timer or event (macrotask). That's why Promises run before setTimeout(…, 0)."),
        ],
        "qa": [
            ("How do you run several API calls at the same time?", "Start them all, then await Promise.all([a(), b(), c()]). They run in parallel and you get all results together; it fails if any one fails."),
            ("What happens if you forget to handle a rejected Promise?", "You get an 'unhandled promise rejection' warning and the error may silently break a feature. Always use try/catch with await, or .catch()."),
            ("Is JavaScript truly single-threaded?", "Your code runs on one main thread, but the browser or Node does I/O in the background, and Web Workers let you run heavy work on extra threads."),
        ],
    },
    "TypeScript Essentials": {
        "simple": [
            ("What TypeScript is", "TypeScript is JavaScript with labels on your data. You say 'this is a number' and the editor warns you before you run the code if you use it wrong."),
            ("Types and interfaces", "An interface describes the shape of an object, like a form with required fields: name is a string, age is a number. Both type and interface work for this."),
            ("Union types", "A union says 'one of these': size: 'sm' | 'md' | 'lg'. TypeScript then blocks typos like 'medium'."),
            ("Generics", "Generics are placeholders for types. A box that can hold 'any one type, decided later': Array<number> or Array<string>."),
            ("Narrowing", "When a value could be several types, checks like typeof x === 'string' tell TypeScript which one it is inside that if-block."),
        ],
        "qa": [
            ("Do TypeScript types exist at runtime?", "No. They are removed when compiled to JavaScript, so you still need to validate data coming from users or APIs (for example with zod)."),
            ("What is the difference between type and interface?", "Both describe shapes. Interfaces can be extended and merged; type aliases can also describe unions and other combinations. Teams usually pick one style."),
            ("Why is `any` discouraged?", "`any` turns off type checking for that value, so mistakes slip through. Use `unknown` and check the type before using it."),
        ],
    },
    "Python Core & Data Structures": {
        "simple": [
            ("Lists", "A list is an ordered, changeable collection, like a shopping list you can add to and reorder: [1, 2, 3]."),
            ("Tuples", "A tuple is like a list that can't change once created, such as a pair of coordinates (x, y). Because it can't change, it can be used as a dictionary key."),
            ("Dictionaries", "A dict stores key → value pairs, like a phone book: look up 'Asha' and get her number instantly, without scanning every entry."),
            ("Sets", "A set holds unique items with no order. Great for removing duplicates or checking 'have I seen this before?' very quickly."),
            ("Exceptions", "Exceptions are Python's way of saying 'something went wrong'. try/except lets you catch the problem and respond instead of crashing."),
        ],
        "qa": [
            ("How do you remove duplicates from a list but keep the order?", "list(dict.fromkeys(items)). Dictionaries keep insertion order and drop repeated keys."),
            ("What does `is` do compared with `==`?", "`==` checks if two values are equal; `is` checks if they are the very same object in memory. Use `is` mainly for `is None`."),
            ("What is a list comprehension?", "A short way to build a list: [x * 2 for x in nums if x > 0] doubles every positive number in one readable line."),
        ],
    },
    "OOP, Iterators & Generators in Python": {
        "simple": [
            ("Classes and objects", "A class is a blueprint, like a house plan; objects are the actual houses built from it. Each object has its own data but shares the same methods."),
            ("Dunder methods", "Methods with double underscores, like __init__ and __str__, let your objects work with Python's built-ins: creating them, printing them, comparing them."),
            ("Inheritance", "A child class reuses a parent class and can change some behaviour. A Dog class can inherit from Animal and override speak()."),
            ("Generators", "A generator produces values one at a time with `yield`, like a ticket machine that prints the next ticket only when asked. It saves memory on big data."),
            ("Decorators", "A decorator wraps a function to add behaviour without changing its code, such as timing it, logging it or caching its results."),
        ],
        "qa": [
            ("What is `self` in Python?", "`self` is the object the method is being called on. Python passes it automatically, so obj.method() becomes Class.method(obj)."),
            ("Generator vs list: which uses less memory?", "A generator, because it creates items on demand instead of storing them all. A list of a million numbers lives in memory; a generator doesn't."),
            ("What is @dataclass for?", "It auto-writes __init__, __repr__ and __eq__ for classes that mainly store data, saving a lot of boilerplate."),
        ],
    },
    "Python for Data: NumPy & pandas": {
        "simple": [
            ("NumPy arrays", "A NumPy array is a fast grid of numbers. Math on the whole array (arr * 2) runs in optimised C code instead of a slow Python loop."),
            ("DataFrame", "A pandas DataFrame is a table in Python, like an Excel sheet: rows, named columns, and handy operations."),
            ("Selecting data", "df['col'] picks a column; df.loc[] selects by labels and df.iloc[] by positions. Filtering looks like df[df['age'] > 25]."),
            ("groupby", "groupby splits rows into groups and summarises each, like 'average salary per department'. It's pandas' version of SQL GROUP BY."),
            ("Missing values", "Real data has blanks (NaN). isna() finds them, fillna() fills them and dropna() removes them."),
        ],
        "qa": [
            ("How do you join two DataFrames?", "pd.merge(left, right, on='id', how='left') works like a SQL LEFT JOIN: every row from left, with matching data from right."),
            ("Why avoid iterrows()?", "It loops row by row in Python, which is slow. Vectorised operations or .apply on columns are usually far faster."),
            ("What is broadcasting?", "NumPy stretching a smaller array to match a bigger one, so you can add a single number or a row to a whole matrix without loops."),
        ],
    },
    "Language Fundamentals (Java / C++)": {
        "simple": [
            ("Primitive vs reference types", "Primitives (int, double) hold the value directly. Reference types (objects) hold an address pointing to where the object lives, like a house address instead of the house."),
            ("Stack and heap", "Local variables live on the stack, which is fast and cleared when a function ends. Objects live on the heap and stay until no longer used."),
            ("Collections", "Ready-made data structures: ArrayList/vector for lists, HashMap/unordered_map for key-value lookups, HashSet for unique items, PriorityQueue for 'always give me the smallest'."),
            ("Memory management", "Java's garbage collector frees unused objects for you. In C++ you manage memory, ideally with smart pointers that free it automatically."),
            ("Strings", "Java Strings can't be changed after creation, so building a string in a loop should use StringBuilder to avoid creating many copies."),
        ],
        "qa": [
            ("Is Java pass-by-value or pass-by-reference?", "Always pass-by-value. For objects, the value passed is the reference (address), so you can modify the object but not make the caller's variable point elsewhere."),
            ("What's the difference between ArrayList and LinkedList?", "ArrayList is a resizable array: fast index access, slow middle inserts. LinkedList is chained nodes: fast inserts at known positions, slow index access."),
            ("Why override hashCode() with equals()?", "HashMap uses hashCode() to find the bucket and equals() to compare. If equal objects have different hash codes, lookups fail."),
        ],
    },
    "Object-Oriented Design": {
        "simple": [
            ("Encapsulation", "Keep an object's data private and expose safe methods. Like a bank account: you can deposit and withdraw, but can't edit the balance directly."),
            ("Abstraction", "Show what something does, hide how. You press a car's accelerator without knowing how fuel injection works."),
            ("Inheritance", "A class can extend another and reuse its code: a SavingsAccount is an Account with extra rules."),
            ("Polymorphism", "One action, many forms: calling shape.area() gives the right answer whether the shape is a circle or a square."),
            ("SOLID principles", "Five guidelines for code that's easy to change. The most important: each class should have one job, and code should depend on interfaces, not concrete classes."),
        ],
        "qa": [
            ("How would you design a parking lot system?", "Identify entities (ParkingLot, Level, Spot, Vehicle, Ticket), their relationships, and responsibilities like assigning spots and calculating fees; then discuss extensibility, such as new vehicle types."),
            ("When would you use the Strategy pattern?", "When you need to switch algorithms at runtime, such as different payment methods or sorting strategies, without if-else chains."),
            ("What does 'composition over inheritance' mean?", "Build objects by combining smaller parts (has-a) instead of deep class hierarchies (is-a). It's more flexible when requirements change."),
        ],
    },
    "Git & Engineering Workflow": {
        "simple": [
            ("Commit", "A commit is a saved snapshot of your project with a message, like a save point in a game you can return to."),
            ("Branch", "A branch is a separate line of work, so you can build a feature without disturbing the main code."),
            ("Merge", "Merging brings a branch's changes back into another branch. If two people changed the same lines, Git asks you to resolve the conflict."),
            ("Pull request", "A pull request asks teammates to review your branch before it's merged. It's where code review and discussion happen."),
            ("Rebase", "Rebase replays your commits on top of the latest main branch, giving a clean, straight history. Never rebase branches others are using."),
        ],
        "qa": [
            ("How do you undo the last commit but keep the changes?", "git reset --soft HEAD~1. The commit is removed but your changes stay staged."),
            ("What is a merge conflict and how do you fix it?", "It happens when two branches change the same lines. Open the file, choose the right code between the conflict markers, then add and commit."),
            ("What makes a good commit message?", "A short summary of what changed and why, in the imperative mood: 'Fix login timeout when token expires'."),
        ],
    },
    "Arrays, Strings & Hashing": {
        "simple": [
            ("Arrays", "An array stores items side by side in memory, so jumping to item #5 is instant. Inserting in the middle is slow because items must shift."),
            ("Two pointers", "Use two markers moving through the data, often from both ends, to avoid checking every pair. Useful for sorted arrays and palindromes."),
            ("Sliding window", "Keep a 'window' over part of the array and slide it along, adding the new item and removing the old one, instead of recalculating from scratch."),
            ("Hash maps", "A hash map gives near-instant lookups by key. Classic trick: store what you've seen so far to answer 'have I seen the complement?' in one pass."),
            ("Prefix sums", "Precompute running totals once; then the sum of any range is just two subtractions, instead of adding the range each time."),
        ],
        "qa": [
            ("How do you check if two strings are anagrams?", "Count characters in both (a hash map or 26-length array) and compare counts; O(n) time. Sorting both strings also works in O(n log n)."),
            ("Find the longest substring without repeating characters.", "Sliding window with a map of last-seen indexes: expand the right end; when a repeat appears, move the left end past its previous position. O(n)."),
            ("How do you find a duplicate in an array?", "Add items to a set; if an item is already there, it's a duplicate. O(n) time, O(n) space."),
        ],
    },
    "Linked Lists, Stacks & Queues": {
        "simple": [
            ("Linked list", "A chain of nodes where each node points to the next, like a treasure hunt where each clue tells you where the next one is."),
            ("Reversing a list", "Walk the chain and flip each arrow to point backwards, keeping track of the previous, current and next nodes."),
            ("Fast and slow pointers", "Move one pointer one step and another two steps. If there's a loop, they eventually meet, like runners on a circular track."),
            ("Stack", "Last in, first out, like a stack of plates. Perfect for undo, matching brackets and tracking function calls."),
            ("Queue", "First in, first out, like a line at a counter. Used for scheduling tasks and breadth-first search."),
        ],
        "qa": [
            ("How do you find the middle of a linked list in one pass?", "Use slow and fast pointers: when fast reaches the end, slow is at the middle."),
            ("How do you check if brackets are balanced?", "Push each opening bracket onto a stack; for each closing bracket, the top must be its matching opener. The stack must be empty at the end."),
            ("Implement a queue using two stacks.", "Push into stack A. To dequeue, if B is empty, move everything from A to B (reversing order), then pop from B. Each element moves at most once."),
        ],
    },
    "Trees & Binary Search": {
        "simple": [
            ("Tree", "A tree is a hierarchy, like a family tree or folders on a computer: one root, each node has children."),
            ("Binary search tree", "Left children are smaller, right children are bigger. Searching works like guessing a number: each step halves the options."),
            ("Traversals", "Ways to visit every node: inorder (left, node, right) gives sorted order in a BST; level order visits row by row."),
            ("Heaps", "A heap always keeps the smallest (or largest) item on top, like a priority waiting room. Great for 'top K' problems."),
            ("Binary search", "On sorted data, check the middle, then throw away the half that can't contain the answer. A million items take only about 20 steps."),
        ],
        "qa": [
            ("Find the maximum depth of a binary tree.", "Recursively: depth = 1 + max(depth(left), depth(right)), with an empty tree having depth 0."),
            ("How do you validate a BST?", "Pass down allowed min and max bounds: each node must lie strictly within them; left children update the max, right children update the min."),
            ("Search in a rotated sorted array?", "Binary search, but at each step decide which half is properly sorted and whether the target lies in it."),
        ],
    },
    "Graphs: BFS, DFS & Shortest Paths": {
        "simple": [
            ("Graph", "A graph is dots (nodes) connected by lines (edges), like cities and roads, or people and friendships."),
            ("BFS", "Breadth-first search explores neighbours first, ring by ring, like ripples in a pond. It finds the shortest path when all edges cost the same."),
            ("DFS", "Depth-first search goes as deep as possible before backtracking, like exploring a maze by always taking the next turn."),
            ("Visited set", "Remember which nodes you've seen so you don't loop forever in graphs with cycles."),
            ("Dijkstra's algorithm", "Finds the cheapest path when roads have different costs, always expanding the cheapest known place next using a priority queue."),
        ],
        "qa": [
            ("How do you detect a cycle in a directed graph?", "DFS with three colours (unvisited, visiting, done). Reaching a 'visiting' node again means a cycle. Or use Kahn's topological sort."),
            ("What is a topological sort used for?", "Ordering tasks with dependencies, like course prerequisites or build steps, so every task comes after what it depends on."),
            ("Why doesn't Dijkstra work with negative edges?", "It assumes once a node is finalised its distance can't improve; a negative edge could later make it cheaper. Use Bellman-Ford instead."),
        ],
    },
    "Dynamic Programming": {
        "simple": [
            ("The idea", "Dynamic programming means 'don't solve the same small problem twice'. Save answers to sub-problems and reuse them."),
            ("Overlapping subproblems", "If your recursive solution keeps recalculating the same inputs (like fib(3) many times), DP can help."),
            ("Memoization", "Top-down: write the recursion, then add a cache so each input is computed once."),
            ("Tabulation", "Bottom-up: fill a table from the smallest cases up to the answer, like building a staircase step by step."),
            ("State and recurrence", "Decide what dp[i] means in words, then how dp[i] is built from smaller states. That sentence is the heart of every DP solution."),
        ],
        "qa": [
            ("Explain the climbing stairs problem.", "To reach step n you come from n−1 or n−2, so ways(n) = ways(n−1) + ways(n−2), which is the Fibonacci pattern."),
            ("What is the 0/1 knapsack problem?", "Pick items with weights and values to maximise value within a weight limit, each item used at most once. dp[w] = best value with capacity w."),
            ("How do you reduce DP space usage?", "If each state only depends on the previous row or last few values, keep just those instead of the full table."),
        ],
    },
    "Greedy, Backtracking & Bit Tricks": {
        "simple": [
            ("Greedy", "Make the best-looking choice at each step and never look back, like always taking the largest coin for change. It only works when you can prove it's safe."),
            ("Backtracking", "Try a choice, explore, and undo it if it fails, like trying keys on a lock. Used for generating subsets, permutations and puzzles."),
            ("Pruning", "Stop exploring paths that clearly can't succeed, which can turn an impossible search into a fast one."),
            ("Bit manipulation", "Treat numbers as rows of 0s and 1s. Tricks like x & (x−1) remove the lowest 1-bit; XOR cancels equal numbers."),
            ("Intervals", "Many greedy problems are about time slots: sort by end time and keep picking the next meeting that starts after the last one ends."),
        ],
        "qa": [
            ("Generate all subsets of [1,2,3].", "Backtracking: for each element choose include or exclude, giving 2^n subsets; or iteratively add each element to all existing subsets."),
            ("Find the single number when every other appears twice.", "XOR all numbers: pairs cancel to 0, leaving the single one. O(n) time, O(1) space."),
            ("Why doesn't greedy always work for coin change?", "With coins [1, 3, 4] and amount 6, greedy picks 4+1+1 (3 coins) but 3+3 (2 coins) is better. That needs DP."),
        ],
    },
    "Operating Systems": {
        "simple": [
            ("Process", "A running program with its own memory, like a separate apartment."),
            ("Thread", "A worker inside a process; threads share the same memory, like roommates sharing an apartment, which is fast but needs coordination."),
            ("Scheduling", "The OS decides which task gets the CPU next, switching quickly so many programs seem to run at once."),
            ("Virtual memory", "Each program thinks it has a big private memory; the OS maps it to real RAM and disk behind the scenes."),
            ("Deadlock", "Two tasks each hold something the other needs and wait forever, like two cars blocking each other on a narrow bridge."),
        ],
        "qa": [
            ("What is a race condition?", "When the result depends on the timing of threads touching shared data, for example two threads incrementing a counter at once and losing an update. Fix with locks or atomics."),
            ("Mutex vs semaphore?", "A mutex is a single key: one thread at a time. A semaphore is a set of N keys: up to N threads at once."),
            ("What is paging?", "Memory is split into fixed-size pages mapped to physical frames, so a program's memory doesn't need to be contiguous in RAM."),
        ],
    },
    "DBMS & SQL": {
        "simple": [
            ("Tables and keys", "Data lives in tables. A primary key uniquely identifies each row; a foreign key links a row to a row in another table."),
            ("Normalisation", "Organise tables so each fact is stored once, which avoids contradictions when updating data."),
            ("Transactions (ACID)", "A transaction is all-or-nothing, like a bank transfer: money leaves one account and arrives in the other, or neither happens."),
            ("Indexes", "An index is like a book's index: find rows quickly without scanning every page, at the cost of slower writes."),
            ("JOINs", "JOINs combine related tables, such as customers with their orders. LEFT JOIN keeps every customer, even those without orders."),
        ],
        "qa": [
            ("Find the second highest salary.", "SELECT MAX(salary) FROM emp WHERE salary < (SELECT MAX(salary) FROM emp); or use DENSE_RANK() and pick rank 2."),
            ("DELETE vs TRUNCATE vs DROP?", "DELETE removes chosen rows (can be rolled back), TRUNCATE quickly empties the table, DROP removes the table itself."),
            ("What is a deadlock in databases?", "Two transactions each lock rows the other needs. The database detects it and rolls one back; consistent lock ordering prevents it."),
        ],
    },
    "Computer Networks": {
        "simple": [
            ("Layers", "Networking is built in layers, like a postal system: the app writes the letter, TCP makes sure it arrives, IP finds the route, and cables carry it."),
            ("TCP", "A reliable, ordered delivery service, like a phone call: connection first, and anything lost is resent."),
            ("UDP", "Fast, no guarantees, like shouting across a room. Used where speed matters more than perfection: video calls and games."),
            ("DNS", "The internet's phone book: it turns names like google.com into IP addresses."),
            ("HTTPS", "HTTP wrapped in encryption (TLS) so nobody in between can read or change what's sent."),
        ],
        "qa": [
            ("Explain the TCP three-way handshake.", "Client sends SYN, server replies SYN-ACK, client sends ACK. Now both sides agree on starting sequence numbers and the connection is open."),
            ("What's the difference between a router and a switch?", "A switch connects devices within a local network using MAC addresses; a router connects different networks and routes using IP addresses."),
            ("What does HTTP status 404 vs 500 mean?", "404 means the requested resource doesn't exist (client side); 500 means the server crashed or failed while handling the request."),
        ],
    },
    "ATS Resume & Portfolio": {
        "simple": [
            ("What an ATS is", "An Applicant Tracking System is software that reads resumes before humans do. Fancy layouts confuse it, so simple wins."),
            ("Single column", "Use one column, standard headings (Education, Skills, Projects, Experience) and real text, with no tables, icons or images."),
            ("Keywords", "Use the exact words from the job description where they're true for you, like 'React', 'REST APIs' or 'SQL'."),
            ("Impact bullets", "Each bullet should show what you did and the result: 'Built X using Y, which improved Z by 30%'."),
            ("Portfolio", "A clean GitHub with READMEs and live demos lets interviewers see your work. Pin your best 3–4 projects."),
        ],
        "qa": [
            ("How long should a fresher's resume be?", "One page. Keep the most relevant projects and skills; cut anything that doesn't support the role you're applying for."),
            ("Should I include a photo or graphics?", "Not for most tech roles. They can break ATS parsing and take space better used for skills and impact."),
            ("What if I have no work experience?", "Lead with education, projects, hackathons and open source. Describe projects like jobs: problem, what you built, result."),
        ],
    },
    "Behavioral Interviews (STAR)": {
        "simple": [
            ("STAR", "Situation (the context), Task (your goal), Action (what YOU did), Result (what happened). It keeps stories clear and complete."),
            ("Focus on actions", "Spend most of the answer on your actions and decisions. Say 'I', not 'we', so the interviewer knows your contribution."),
            ("End with a result", "Close with a number or clear outcome, plus what you learned: 'We shipped on time and cut bugs by half.'"),
            ("Story bank", "Prepare 6–8 short stories in advance (conflict, failure, leadership, tight deadline, learning something fast) and adapt them to questions."),
            ("Tell me about yourself", "A 60–90 second pitch: who you are now, what you've done (best project), and why this role is your next step."),
        ],
        "qa": [
            ("Tell me about a time you failed.", "Pick a real but recoverable mistake, own it, explain how you fixed it, and show what you changed so it won't happen again."),
            ("How do you handle disagreement with a teammate?", "Listen first, focus on data or user impact, propose a quick test or compromise, and keep the relationship respectful. Give a real example."),
            ("Why should we hire you?", "Connect two or three of your strongest relevant skills or projects to what the role needs, and show enthusiasm for the team's work."),
        ],
    },
    "Mock Interviews & Strategy": {
        "simple": [
            ("Think aloud", "Interviewers grade your thinking, not just the final answer. Narrate what you're considering and why."),
            ("Clarify first", "Ask about input size, edge cases and expected output before coding. It shows maturity and prevents solving the wrong problem."),
            ("Brute force, then optimise", "Start with a simple working idea, state its complexity, then improve it. A correct slow solution beats an unfinished fast one."),
            ("Test your code", "Walk through a small example and edge cases (empty input, one element) before saying you're done."),
            ("Practise regularly", "Weekly mock interviews build calm and speed. Review recordings or feedback and track your weak topics."),
        ],
        "qa": [
            ("What should you do if you get stuck?", "Explain what you've tried, go back to brute force, work through an example by hand, and ask for a hint. Getting unstuck gracefully earns credit."),
            ("How do you manage time in a 45-minute coding round?", "About 5 minutes clarifying, 10 planning, 20 coding and 10 testing and discussing optimisations."),
            ("What questions should you ask at the end?", "Ask about the team's current challenges, what success looks like in the first months, and how the team grows engineers."),
        ],
    },
}
