"""Beginner-friendly explanations and extra interview Q&A: frontend and backend web development."""

NOTES = {
    "Semantic HTML & Accessibility": {
        "simple": [
            ("Semantic tags", "Use tags that describe meaning, such as <header>, <nav>, <main>, <article>, <button>, instead of plain <div>s everywhere. Browsers, search engines and screen readers understand the page better."),
            ("Accessibility (a11y)", "Making sites usable by everyone, including people using screen readers, keyboards only, or with low vision."),
            ("Alt text", "Every meaningful image needs a short description in its alt attribute, so screen-reader users know what it shows."),
            ("Forms", "Connect every input to a <label>. Then clicking the label focuses the input, and screen readers announce what the field is for."),
            ("Keyboard navigation", "Everything clickable must work with Tab and Enter. Real <button> and <a> elements do this for free."),
        ],
        "qa": [
            ("What is ARIA and when should you use it?", "ARIA attributes add meaning that HTML can't express, like live regions or custom widgets. Use native HTML first; add ARIA only for gaps."),
            ("How do you test accessibility?", "Navigate using only the keyboard, run Lighthouse or axe, check colour contrast, and try a screen reader like NVDA or VoiceOver."),
            ("Why is a heading order important?", "Screen-reader users jump between headings to navigate. A logical h1 → h2 → h3 order works like a table of contents."),
        ],
    },
    "CSS Layout: Flexbox, Grid & Responsive Design": {
        "simple": [
            ("Box model", "Every element is a box: content, then padding (inner space), border, then margin (outer space). box-sizing: border-box makes widths include padding and border."),
            ("Flexbox", "Arranges items in one direction, a row or a column. Great for navbars, centring things, and spacing items evenly."),
            ("Grid", "Arranges items in rows and columns at the same time, like a spreadsheet. Great for full page layouts and card galleries."),
            ("Responsive design", "Pages adapt to screen size. Design for mobile first, then add media queries for bigger screens."),
            ("Specificity", "When CSS rules conflict, the more specific selector wins: id beats class, and class beats a tag name."),
        ],
        "qa": [
            ("How do you centre a div?", "On the parent, use display: flex; justify-content: center; align-items: center; or display: grid; place-items: center."),
            ("What's the difference between em and rem?", "rem is relative to the root font size and stays consistent; em is relative to the parent's font size and can compound."),
            ("What does position: sticky do?", "The element scrolls normally until it reaches a set offset (like top: 0), then sticks there while its container is visible."),
        ],
    },
    "Browser Internals & the DOM": {
        "simple": [
            ("The DOM", "The browser turns HTML into a tree of objects (the DOM) that JavaScript can read and change."),
            ("Rendering steps", "HTML → DOM, CSS → styles, then layout (where things go), paint (draw pixels) and composite (stack layers)."),
            ("Reflow", "Changing size or position makes the browser recalculate the layout, which is expensive. Too many reflows make pages janky."),
            ("Event bubbling", "A click on a button also 'bubbles up' to its parents. That lets one listener on a parent handle clicks for many children."),
            ("Browser storage", "localStorage keeps small data even after closing the tab, sessionStorage only for the tab, cookies are sent to the server, and IndexedDB stores big structured data."),
        ],
        "qa": [
            ("What's the difference between defer and async on scripts?", "Both download in parallel. async runs as soon as it's downloaded (order not guaranteed); defer runs after HTML parsing, in order."),
            ("What is event delegation?", "Attaching one listener to a parent and using event.target to handle clicks on its children, including ones added later."),
            ("Why animate transform instead of top/left?", "transform and opacity can be handled by the GPU without layout recalculation, so animations stay smooth."),
        ],
    },
    "React Fundamentals & Hooks": {
        "simple": [
            ("Components", "A component is a reusable piece of UI, like a LEGO brick: a function that returns what should appear on screen."),
            ("Props", "Props are inputs passed from parent to child, like arguments to a function. The child shouldn't change them."),
            ("State", "State is data a component remembers and can change, like a counter's value. Changing state makes React re-render."),
            ("useEffect", "useEffect runs code after rendering, for things like fetching data or subscribing to events. Its dependency list says when to run again."),
            ("Keys in lists", "Give each list item a stable, unique key (like an id) so React can track items when the list changes."),
        ],
        "qa": [
            ("Why shouldn't you modify state directly?", "React detects changes by comparing references. Mutating an object keeps the same reference, so React may not re-render. Create a new object or array instead."),
            ("What is the virtual DOM?", "A lightweight copy of the UI in memory. React compares the new copy with the old one and updates only what changed in the real DOM."),
            ("Controlled vs uncontrolled inputs?", "Controlled inputs store their value in React state (value + onChange). Uncontrolled inputs keep their own value and you read it with a ref."),
        ],
    },
    "State Management & Data Fetching": {
        "simple": [
            ("Local first", "Keep state in the component that uses it. Only move it up when other components need it too."),
            ("Lifting state up", "If two siblings need the same data, store it in their closest common parent and pass it down as props."),
            ("Context", "Context shares data like theme or logged-in user without passing props through every level."),
            ("Global stores", "Redux or Zustand hold shared app state in one place with clear rules for how it changes, which helps in big apps."),
            ("Server state", "Data from an API is different from UI state. Tools like React Query cache it, refetch it and handle loading and errors for you."),
        ],
        "qa": [
            ("What is prop drilling?", "Passing props through many components that don't use them, just to reach a deep child. Context or a store avoids it."),
            ("How do you avoid a race condition when fetching data in useEffect?", "Use an AbortController (or an 'ignore' flag) in the cleanup function so a slow old request can't overwrite newer data."),
            ("When is Redux overkill?", "In small or medium apps where state is mostly local or server data. React state plus React Query is often enough."),
        ],
    },
    "Next.js & Rendering Strategies": {
        "simple": [
            ("CSR", "Client-side rendering: the browser gets an almost empty page and JavaScript builds it. Simple, but slower first load and weaker SEO."),
            ("SSR", "Server-side rendering: the server builds the HTML on every request, so users and search engines see content immediately."),
            ("SSG", "Static generation: pages are built once at deploy time and served instantly from a CDN. Ideal for blogs and docs."),
            ("ISR", "Incremental static regeneration: static pages that quietly rebuild every few minutes, so you get speed and fairly fresh data."),
            ("Hydration", "After server HTML arrives, React attaches event handlers so the page becomes interactive. The server and client HTML must match."),
        ],
        "qa": [
            ("What are React Server Components?", "Components that run only on the server, can fetch data directly, and send no JavaScript to the browser, which makes pages lighter."),
            ("How do you choose a rendering strategy for a product page?", "Use SSG or ISR for speed and SEO, and fetch fast-changing info like stock or price on the client or with SSR."),
            ("What causes a hydration mismatch?", "Rendering different content on the server and client, such as using Date.now(), Math.random() or window during render."),
        ],
    },
    "Web Performance & Core Web Vitals": {
        "simple": [
            ("LCP", "Largest Contentful Paint: how fast the main content (often a big image or heading) appears. Aim for under 2.5 seconds."),
            ("INP", "Interaction to Next Paint: how quickly the page responds when you click or type. Aim for under 200 ms."),
            ("CLS", "Cumulative Layout Shift: how much things jump around while loading. Reserve space for images and ads to keep it low."),
            ("Smaller bundles", "Ship less JavaScript: split code by page, remove unused libraries, and load heavy parts only when needed."),
            ("Images", "Use modern formats (WebP, AVIF), the right size for the screen, and lazy-load images below the fold."),
        ],
        "qa": [
            ("How do you find what's slowing a page down?", "Run Lighthouse or the DevTools Performance tab, check the LCP element, the network waterfall and long JavaScript tasks."),
            ("What is code splitting?", "Breaking your JavaScript into chunks loaded on demand (for example per route with dynamic import), so the first load is smaller."),
            ("Why use a CDN?", "It serves files from servers close to the user, cutting delay, and caches static assets so your origin server does less work."),
        ],
    },
    "Frontend Security": {
        "simple": [
            ("XSS", "Cross-site scripting: an attacker sneaks their JavaScript into your page, for example through a comment box, and it runs in other users' browsers."),
            ("Escaping", "Treat user input as text, never as code. React escapes text by default; be careful with dangerouslySetInnerHTML."),
            ("CSRF", "Cross-site request forgery: a malicious site makes your logged-in browser send a request to another site. SameSite cookies and CSRF tokens stop it."),
            ("CORS", "The browser blocks pages from reading responses from other origins unless that server allows it. It protects users, not your API."),
            ("Secrets", "Anything in frontend code is public. Never put API keys or passwords there; keep them on the server."),
        ],
        "qa": [
            ("What is a Content Security Policy?", "An HTTP header listing where scripts, styles and images may load from. It blocks injected scripts even if an XSS bug exists."),
            ("Where should you store auth tokens?", "Prefer HttpOnly, Secure, SameSite cookies, which JavaScript can't read. localStorage is readable by any script, so XSS can steal it."),
            ("Does HTTPS prevent XSS?", "No. HTTPS protects data in transit; XSS is about untrusted content running in the page. You need escaping and CSP too."),
        ],
    },
    "Testing Frontend Apps": {
        "simple": [
            ("Unit tests", "Test small pieces, like a function that formats dates, in isolation. They're fast and pinpoint bugs."),
            ("Component tests", "Render a component and interact with it the way a user would: click buttons, type text, check what appears."),
            ("End-to-end tests", "A robot browser (Playwright, Cypress) clicks through real flows like sign-up and checkout."),
            ("Mocking", "Replace real network calls with fake responses so tests are fast and reliable."),
            ("Test behaviour", "Check what the user sees, not internal details, so tests keep passing when you refactor."),
        ],
        "qa": [
            ("What is the testing pyramid?", "Many fast unit tests at the bottom, fewer integration tests in the middle, and a small number of slow end-to-end tests on top."),
            ("Why query by role or label in Testing Library?", "It mirrors how real users and screen readers find elements, and it encourages accessible markup."),
            ("How do you test loading and error states?", "Mock the API to delay or fail, then assert that the spinner or error message appears."),
        ],
    },
    "REST API Design": {
        "simple": [
            ("Resources", "Everything is a resource with a URL, using nouns: /users, /users/42/orders."),
            ("HTTP methods", "GET reads, POST creates, PUT replaces, PATCH updates part, DELETE removes, like verbs acting on the nouns."),
            ("Status codes", "2xx = success, 4xx = the client did something wrong, 5xx = the server failed. 201 Created, 400 Bad Request, 401/403 for auth, 404 Not Found."),
            ("Stateless", "Each request carries everything needed (like the auth token), so any server can handle it. This makes scaling easy."),
            ("Pagination", "Return big lists in pages (?limit=20&cursor=…) so responses stay small and fast."),
        ],
        "qa": [
            ("What does idempotent mean?", "Repeating the request has the same effect as doing it once. GET, PUT and DELETE are idempotent; POST is not."),
            ("How do you version an API?", "Put the version in the URL (/v1/) or a header, and keep old versions working until clients migrate."),
            ("401 vs 403?", "401 means 'we don't know who you are' (not logged in). 403 means 'we know who you are, but you're not allowed'."),
        ],
    },
    "Building APIs (FastAPI / Express / Spring)": {
        "simple": [
            ("Routes", "A route connects a URL and method to a function: GET /users/42 → get_user(42)."),
            ("Validation", "Check every input at the door, such as types, required fields and limits, so bad data never reaches your logic."),
            ("Middleware", "Code that runs on every request before or after your route, for logging, authentication or CORS."),
            ("Layers", "Keep route handlers thin: they parse input and return output, while services hold the business logic."),
            ("Error handling", "Return clear, consistent error messages with the right status code instead of crashing."),
        ],
        "qa": [
            ("Why use async endpoints?", "While one request waits for the database or another API, the server can handle other requests, which improves throughput for I/O-heavy apps."),
            ("How do you structure a medium-sized backend?", "Split into routers (HTTP), services (business logic), repositories (database access) and schemas (validation), with configuration from environment variables."),
            ("How do you handle configuration secrets?", "Load them from environment variables or a secrets manager, never hard-code them or commit them to git."),
        ],
    },
    "Authentication & Authorization": {
        "simple": [
            ("Authentication", "Proving who you are, like showing your ID at the door."),
            ("Authorization", "Deciding what you're allowed to do once inside, like which rooms your badge opens."),
            ("Password hashing", "Never store passwords. Store a slow, salted hash (bcrypt, Argon2) so a leaked database doesn't reveal them."),
            ("Sessions vs JWTs", "Sessions keep login info on the server and give the browser a cookie ID. JWTs are signed tokens the server can verify without a lookup."),
            ("OAuth / 'Sign in with Google'", "Google confirms who the user is and gives your app a signed token; your server verifies it and logs the user in."),
        ],
        "qa": [
            ("How do refresh tokens work?", "Access tokens are short-lived. When one expires, the app uses a longer-lived refresh token to get a new one without asking the user to log in again."),
            ("What is role-based access control?", "Users get roles (admin, editor, viewer) and each role has permissions. Check permissions on the server for every request."),
            ("How do you protect a login endpoint from attacks?", "Rate-limit attempts, add MFA, use generic error messages, and monitor for credential stuffing."),
        ],
    },
    "Relational Modelling & SQL Mastery": {
        "simple": [
            ("Entities and relationships", "Find the 'things' (users, orders, products) and how they relate: one user has many orders; orders and products are many-to-many."),
            ("Many-to-many", "Use a join table, such as order_items(order_id, product_id, quantity), to connect two tables."),
            ("Constraints", "Let the database enforce rules: NOT NULL, UNIQUE, FOREIGN KEY. It's a safety net if your code has bugs."),
            ("N+1 problem", "Loading 100 users and then running a separate query for each user's orders means 101 queries. Use a JOIN or eager loading instead."),
            ("EXPLAIN", "Ask the database how it plans to run a query, to see whether it scans the whole table or uses an index."),
        ],
        "qa": [
            ("What is a CTE?", "A Common Table Expression (WITH name AS (...)) is a named temporary result that makes long queries readable, like variables for SQL."),
            ("When would you denormalise?", "When reads are heavy and joins are slow, for example storing a precomputed order total, accepting extra work to keep it in sync."),
            ("How do you model a 'follows' relationship like on Instagram?", "A table follows(follower_id, followee_id) with a unique pair and indexes on both columns for fast lookups in either direction."),
        ],
    },
    "Indexes, Transactions & Concurrency": {
        "simple": [
            ("Index", "A sorted lookup structure (usually a B-tree) that lets the database jump to matching rows instead of reading every row."),
            ("Trade-off", "Indexes make reads faster but writes slower and use extra space, so index the columns you filter and sort by most."),
            ("Composite index", "An index on several columns, like (country, city). It helps queries that filter by country, or by country and city, but not by city alone."),
            ("Isolation levels", "How much concurrent transactions can see each other's unfinished work. Stricter levels are safer but slower."),
            ("Locking", "To stop two people buying the last ticket, lock the row (SELECT … FOR UPDATE) or use a version number and retry on conflict."),
        ],
        "qa": [
            ("What is a dirty read?", "Reading data another transaction changed but hasn't committed. If it rolls back, you read something that never really existed."),
            ("Optimistic vs pessimistic locking?", "Pessimistic locks the row before changing it (good with high contention). Optimistic checks a version number when saving and retries if it changed (good with low contention)."),
            ("Why can too many indexes hurt?", "Every insert, update or delete must update each index, which slows writes and uses more storage and memory."),
        ],
    },
    "NoSQL & Caching (MongoDB, Redis)": {
        "simple": [
            ("Document databases", "MongoDB stores JSON-like documents. Related data can live together in one document, so one read gets everything."),
            ("Embed vs reference", "Embed data that's always read together (a post's comments preview); reference data that's large or shared (the author's full profile)."),
            ("Redis", "An in-memory key-value store that is extremely fast. Used for caching, sessions, counters and queues."),
            ("Cache-aside", "Check the cache first; on a miss, read the database and store the result in the cache with an expiry time."),
            ("CAP theorem", "When the network splits, a distributed database must choose between always answering (availability) and always being correct (consistency)."),
        ],
        "qa": [
            ("How do you keep a cache from showing stale data?", "Set a TTL, delete or update the cache key whenever the data changes, and for critical data read from the database."),
            ("What is a cache stampede?", "When a popular key expires and thousands of requests hit the database at once. Prevent it with locks, staggered TTLs or background refresh."),
            ("When would you choose MongoDB over PostgreSQL?", "For flexible, evolving document data and simple access patterns. PostgreSQL is better for complex relationships, joins and strict consistency."),
        ],
    },
    "System Design Fundamentals": {
        "simple": [
            ("Vertical vs horizontal scaling", "Vertical: buy a bigger machine. Horizontal: add more machines. Horizontal scales further but needs stateless servers."),
            ("Load balancer", "A traffic cop that spreads requests across servers and stops sending to ones that are unhealthy."),
            ("Replication", "Copies of the database: one main copy handles writes and replicas handle reads, which spreads the load and adds backup."),
            ("Sharding", "Splitting data across several databases, for example users A–M on one and N–Z on another, when one machine isn't enough."),
            ("Caching and CDNs", "Keep frequently used data close to users and in memory, so most requests never reach the database."),
        ],
        "qa": [
            ("How do you start a system design interview?", "Clarify requirements and scale, estimate traffic and storage, sketch the API and data model, draw the high-level design, then dive into bottlenecks."),
            ("What is a single point of failure?", "A component whose failure takes the whole system down. Remove it with redundancy: multiple servers, replicas, multiple zones."),
            ("How would you estimate requests per second?", "Daily active users × actions per user ÷ 86,400 seconds, then multiply by 2–3 for peak traffic."),
        ],
    },
    "Message Queues & Async Processing": {
        "simple": [
            ("Queue", "A to-do list between services: one side adds jobs, workers take them one by one. The sender doesn't wait."),
            ("Why queues", "Slow tasks like emails, reports or image resizing shouldn't make users wait. Put them in a queue and respond immediately."),
            ("Pub/sub", "One event, many listeners: 'order placed' can trigger email, analytics and inventory at the same time."),
            ("Retries", "If a job fails, try again later, waiting longer each time (exponential backoff)."),
            ("Idempotency", "A job may run twice, so design it so running twice does no harm, for example by checking whether the email was already sent."),
        ],
        "qa": [
            ("What is a dead-letter queue?", "A separate queue for jobs that keep failing after several retries, so they don't block others and can be inspected later."),
            ("Kafka vs RabbitMQ?", "RabbitMQ is a classic message queue that removes messages once consumed. Kafka is an ordered log that keeps messages, so many consumers can replay them; it's built for huge event streams."),
            ("How do you keep message order?", "Use a single partition or queue per ordering key (for example per user) and process messages from it sequentially."),
        ],
    },
    "Classic Design Problems": {
        "simple": [
            ("URL shortener", "Turn long URLs into short codes: generate a unique ID, encode it in base62, store code → URL, and cache popular links."),
            ("Rate limiter", "Limit how often each user can call an API, like a token bucket that refills slowly. Counters live in Redis so all servers share them."),
            ("News feed", "Either push new posts to followers' feeds when posted, or build the feed when someone opens the app. Celebrities with millions of followers need special handling."),
            ("Chat system", "WebSockets keep a live connection; messages go to a database and through pub/sub to whichever server holds the receiver's connection."),
            ("Trade-offs", "There's no single right answer. Explain why you chose each piece and what you'd change at larger scale."),
        ],
        "qa": [
            ("How do you avoid collisions in a URL shortener?", "Generate codes from a unique counter or ID generator rather than random hashes, and add a unique constraint as a safety net."),
            ("How would you design notifications?", "Events go into a queue; workers check user preferences and send via email, push or SMS providers, with retries and deduplication."),
            ("How do you design for read-heavy traffic?", "Add caching at several layers, read replicas, CDNs for static content, and denormalised views for common queries."),
        ],
    },
    "Testing Backend Services": {
        "simple": [
            ("Unit tests", "Test one function or class alone, replacing the database and other services with fakes."),
            ("Integration tests", "Test pieces working together, like your API with a real (temporary) database."),
            ("Fixtures", "Reusable setup data, such as a test user or sample products, so each test starts from a known state."),
            ("Test the edges", "Check invalid input, missing data and errors, not just the happy path."),
            ("CI", "Run all tests automatically on every pull request, so broken code never reaches main."),
        ],
        "qa": [
            ("What is mocking?", "Replacing a real dependency (like a payment API) with a fake that returns controlled answers, so tests are fast and predictable."),
            ("How much code coverage is enough?", "Coverage is a hint, not a goal. Aim to cover important business logic and risky paths; 70–80% is a common healthy range."),
            ("What makes a test flaky, and how do you fix it?", "Depending on timing, randomness, shared state or the network. Fix it by controlling time, isolating data and mocking external calls."),
        ],
    },
    "Docker & Containers": {
        "simple": [
            ("Container", "A container packages your app with everything it needs, so it runs the same on any machine. No more 'works on my laptop'."),
            ("Image", "An image is the recipe or snapshot; a container is a running instance of it."),
            ("Dockerfile", "A text file with the steps to build an image: base image, copy files, install dependencies, start command."),
            ("Layer caching", "Docker reuses unchanged steps, so copy dependency files and install them before copying your code to make rebuilds fast."),
            ("docker compose", "Starts several containers together (app, database, cache) with one command, which is great for local development."),
        ],
        "qa": [
            ("Container vs virtual machine?", "Containers share the host's operating system kernel, so they're lightweight and start in seconds. VMs include a full OS, so they're heavier but more isolated."),
            ("How do you keep images small?", "Use slim or alpine base images, multi-stage builds, a .dockerignore, and remove build tools from the final image."),
            ("How do you persist data from a container?", "Use volumes, because a container's own filesystem disappears when it's removed."),
        ],
    },
    "CI/CD & Cloud Deployment": {
        "simple": [
            ("CI", "Continuous integration: every push automatically builds and tests the code, catching problems early."),
            ("CD", "Continuous delivery or deployment: tested code is automatically released to staging or production."),
            ("Pipeline", "The sequence of steps, such as lint → test → build → deploy, defined in a file like a GitHub Actions workflow."),
            ("Managed services", "Let the cloud run databases, storage and queues for you so you spend less time on maintenance."),
            ("Rollback", "If a release breaks something, quickly return to the previous version. Always have a rollback plan."),
        ],
        "qa": [
            ("What should a CI pipeline include?", "Install dependencies, lint, run tests, check security, build an artifact or image, and report results on the pull request."),
            ("How do you deploy without downtime?", "Rolling updates, blue-green or canary deployments behind a load balancer, plus health checks before sending traffic."),
            ("How do you manage environments (dev, staging, prod)?", "Use the same build artifact everywhere with configuration from environment variables, and keep infrastructure as code."),
        ],
    },
}
