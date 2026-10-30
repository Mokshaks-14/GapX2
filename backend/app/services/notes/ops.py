"""Beginner-friendly explanations and extra interview Q&A: DevOps/cloud, mobile and security."""

NOTES = {
    "Linux Command Line & Administration": {
        "simple": [
            ("Everything is a file", "In Linux, settings, logs and even devices appear as files, so a few commands work on almost everything."),
            ("Permissions", "Each file says who can read (r), write (w) and execute (x): the owner, the group, and everyone else."),
            ("Processes", "ps and top show running programs; kill stops one by its process ID."),
            ("Services", "systemctl starts, stops and checks background services like web servers; journalctl shows their logs."),
            ("Pipes", "Chain commands with |, for example cat log | grep ERROR | wc -l counts error lines."),
        ],
        "qa": [
            ("How do you find which process uses port 8080?", "ss -tulpn | grep 8080 or lsof -i :8080, then check the process ID."),
            ("What does chmod 644 mean?", "Owner can read and write (6), group can read (4), others can read (4). Typical for normal files."),
            ("How do you follow a log file live?", "tail -f /var/log/app.log shows new lines as they're written."),
        ],
    },
    "Networking for DevOps": {
        "simple": [
            ("IP and ports", "An IP address finds the machine; a port finds the program on it, like a building address plus a flat number."),
            ("DNS records", "A records map names to IPs, CNAMEs are aliases to other names, MX records route email."),
            ("Load balancing", "Spreads traffic across servers. Layer 4 looks at IPs and ports; layer 7 understands HTTP paths and headers."),
            ("Firewalls", "Rules that allow or block traffic by IP, port and protocol, so only what's needed is open."),
            ("TLS certificates", "Prove a server's identity and enable encryption. Tools like Let's Encrypt issue them for free."),
        ],
        "qa": [
            ("How do you debug 'site not loading'?", "Check DNS (dig), network reachability (ping, traceroute), the port (curl -v or nc), then the server and its logs."),
            ("What is a CIDR block like 10.0.0.0/24?", "A range of addresses: /24 means the first 24 bits are fixed, giving 256 addresses (10.0.0.0–10.0.0.255)."),
            ("What's a reverse proxy?", "A server like Nginx that sits in front of apps, forwarding requests and handling TLS, caching and load balancing."),
        ],
    },
    "Scripting & Automation (Bash / Python)": {
        "simple": [
            ("Why automate", "If you do a task more than twice, script it. Scripts are faster, repeatable and document how things are done."),
            ("Bash basics", "Variables, loops and if-statements let you combine commands into small programs."),
            ("Exit codes", "Every command returns 0 for success and anything else for failure; scripts should check these."),
            ("Fail fast", "set -euo pipefail makes a Bash script stop at the first error instead of carrying on and causing damage."),
            ("Python for bigger tasks", "Use Python when logic grows, for APIs, JSON or cloud SDKs like boto3."),
        ],
        "qa": [
            ("How do you schedule a script to run daily?", "Add a cron entry such as 0 2 * * * /path/script.sh (2 AM every day), or use a systemd timer."),
            ("What does idempotent mean for scripts?", "Running it twice gives the same result as once. For example, create a folder only if it doesn't exist."),
            ("Why quote variables in Bash?", "Unquoted variables split on spaces and expand wildcards, so a filename like 'my file.txt' breaks. Use \"$VAR\"."),
        ],
    },
    "Docker in Depth": {
        "simple": [
            ("Images and layers", "Each Dockerfile step creates a layer. Unchanged layers are reused, so ordering steps well speeds up builds."),
            ("Multi-stage builds", "Build in one big image, then copy only the final app into a small clean image."),
            ("Networking", "Containers on the same Docker network can reach each other by container name."),
            ("Volumes", "Store data outside the container so it survives restarts and upgrades."),
            ("Security", "Run as a non-root user, use minimal base images and scan images for known vulnerabilities."),
        ],
        "qa": [
            ("CMD vs ENTRYPOINT?", "ENTRYPOINT is the fixed command; CMD gives default arguments that can be overridden when running the container."),
            ("Why is my image so large?", "Usually a heavy base image, build tools left in, or copying unnecessary files. Use slim images, multi-stage builds and .dockerignore."),
            ("How do containers isolate apps?", "Linux namespaces give each container its own view of processes, network and files; cgroups limit CPU and memory."),
        ],
    },
    "Kubernetes Core Concepts": {
        "simple": [
            ("Pod", "The smallest unit: one or more containers that run together and share a network."),
            ("Deployment", "Keeps a chosen number of pods running and handles updates. If a pod dies, it starts a new one."),
            ("Service", "A stable address for a group of pods, spreading traffic between them even as pods come and go."),
            ("Probes", "Liveness checks restart stuck containers; readiness checks decide when a pod can receive traffic."),
            ("Autoscaling", "The Horizontal Pod Autoscaler adds or removes pods based on CPU or other metrics."),
        ],
        "qa": [
            ("What happens when you run kubectl apply on a deployment?", "Kubernetes compares desired vs current state and performs a rolling update, creating new pods and removing old ones gradually."),
            ("ConfigMap vs Secret?", "Both inject configuration. Secrets are meant for sensitive values and can be encrypted and access-restricted."),
            ("How do you debug a crashing pod?", "kubectl describe pod (events), kubectl logs (and --previous), check probes, resources and image tags."),
        ],
    },
    "CI/CD Pipelines": {
        "simple": [
            ("Pipeline stages", "Typical flow: install → lint → test → build → security scan → deploy."),
            ("Fail fast", "Put quick checks first so developers get feedback in minutes."),
            ("Artifacts", "Build once (for example a Docker image) and deploy that same artifact to every environment."),
            ("Secrets", "Store keys in the CI platform's secret store, never in the repository."),
            ("Deployment strategies", "Rolling, blue-green or canary releases reduce risk and allow quick rollback."),
        ],
        "qa": [
            ("How do you speed up a slow pipeline?", "Cache dependencies, run jobs in parallel, run only affected tests, and use smaller base images."),
            ("What is a canary release?", "Send a small percentage of traffic to the new version, watch error rates and latency, then gradually increase."),
            ("Why build once and promote?", "So production runs exactly what was tested, avoiding 'it worked in staging' differences."),
        ],
    },
    "Terraform & IaC": {
        "simple": [
            ("Infrastructure as code", "Describe servers, networks and databases in files instead of clicking in a console, so it's repeatable and reviewable."),
            ("Declarative", "You describe what you want (3 servers); Terraform figures out how to get there."),
            ("Plan and apply", "terraform plan previews changes; terraform apply makes them. Always read the plan first."),
            ("State", "Terraform keeps a state file mapping your code to real resources. Store it remotely with locking for teams."),
            ("Modules", "Reusable building blocks, like a standard 'web app + database' setup used across projects."),
        ],
        "qa": [
            ("What happens if two people run terraform apply at the same time?", "Without state locking they can corrupt the state; remote backends with locking prevent this."),
            ("What is configuration drift?", "When real infrastructure differs from the code because someone changed it manually. terraform plan reveals it."),
            ("Terraform vs Ansible?", "Terraform provisions infrastructure (create servers, networks); Ansible configures what runs on them (install packages, edit configs)."),
        ],
    },
    "Cloud Fundamentals (AWS / Azure / GCP)": {
        "simple": [
            ("Compute", "Rent computers by the hour (EC2 / VMs), run containers (ECS, EKS) or just run functions (Lambda) without managing servers."),
            ("Storage", "Object storage (S3) for files, block storage for disks, and managed databases for structured data."),
            ("Networking", "A VPC is your private network in the cloud, split into public and private subnets."),
            ("IAM", "Identity and access management: give people and services only the permissions they need."),
            ("Regions and zones", "Run across several availability zones so one data-centre failure doesn't take you down."),
        ],
        "qa": [
            ("Why put databases in private subnets?", "So they can't be reached directly from the internet; only your app servers can talk to them."),
            ("What is serverless and when is it a good fit?", "Your code runs on demand and scales automatically, paying per use. Great for spiky or event-driven workloads; less ideal for long-running heavy jobs."),
            ("How do you control cloud costs?", "Right-size instances, use auto-scaling, shut down idle resources, use reserved or spot pricing, and set budget alerts."),
        ],
    },
    "Monitoring, Logging & Tracing": {
        "simple": [
            ("Metrics", "Numbers over time, like requests per second, error rate and CPU, which are great for dashboards and alerts."),
            ("Logs", "Detailed event records. Structured (JSON) logs with request IDs make searching easy."),
            ("Traces", "Follow one request across many services to see where time is spent."),
            ("Golden signals", "Latency, traffic, errors and saturation: watch these four for any service."),
            ("Useful alerts", "Alert on what users feel (errors, slowness), not on every CPU spike, to avoid alert fatigue."),
        ],
        "qa": [
            ("Why use percentiles instead of averages for latency?", "Averages hide slow requests. p95 or p99 shows how the slowest users experience the system."),
            ("What is observability?", "Being able to understand a system's inner state from its outputs (metrics, logs, traces), even for problems you didn't predict."),
            ("How do you trace a slow request?", "Use distributed tracing (OpenTelemetry) to see each service's time, then dig into the slowest span's logs and queries."),
        ],
    },
    "SRE Practices & Incident Response": {
        "simple": [
            ("SLI, SLO, SLA", "An SLI is a measurement (latency), an SLO is your target (99.9% under 300 ms), and an SLA is a promise to customers with penalties."),
            ("Error budget", "The allowed unreliability, for example 0.1% of requests. While budget remains you can ship fast; when it's used up, focus on stability."),
            ("Incident response", "Detect, assign roles, communicate, mitigate first (rollback), then find the root cause."),
            ("Postmortem", "A blameless write-up of what happened, why, and what will prevent it next time."),
            ("Toil", "Repetitive manual work. SREs automate it away."),
        ],
        "qa": [
            ("How much downtime does 99.9% allow?", "About 43 minutes per month, or roughly 8.7 hours per year."),
            ("What are the first steps in an outage?", "Acknowledge, assess impact, communicate status, mitigate (rollback or failover), then investigate once users are safe."),
            ("Why blameless postmortems?", "People share honestly when they won't be punished, which reveals the real system and process gaps."),
        ],
    },
    "Kotlin / Swift / Dart Language Essentials": {
        "simple": [
            ("Null safety", "The compiler forces you to handle values that might be missing, preventing the classic 'null pointer' crash."),
            ("Immutability", "Prefer val (Kotlin), let (Swift) or final (Dart) for values that shouldn't change; it makes code safer and easier to reason about."),
            ("Data classes", "Short classes for holding data, with equality and copying built in."),
            ("Lambdas", "Small inline functions you pass around, used for callbacks and list operations like map and filter."),
            ("Async code", "Kotlin coroutines, Swift async/await and Dart futures let you write background work that reads like normal code."),
        ],
        "qa": [
            ("What does ?. and ?: do in Kotlin?", "?. calls only if the value isn't null (safe call); ?: provides a default if it is null (Elvis operator)."),
            ("What is a coroutine?", "A lightweight task that can pause and resume without blocking a thread, so thousands can run cheaply."),
            ("Struct vs class in Swift?", "Structs are value types (copied when assigned); classes are reference types (shared). Swift prefers structs for simple data."),
        ],
    },
    "App Lifecycle & Components": {
        "simple": [
            ("Lifecycle", "Screens move through states: created, visible, in the foreground, paused, stopped, destroyed. The OS decides when."),
            ("Why it matters", "Start and stop things like the camera, location and listeners at the right moments to save battery and avoid crashes."),
            ("Rotation", "On Android, rotating the screen recreates the screen. Keep data in a ViewModel so it survives."),
            ("Process death", "The OS may kill your app in the background. Save important state so the user returns to where they were."),
            ("Permissions", "Ask for camera or location only when needed, explaining why."),
        ],
        "qa": [
            ("onPause vs onStop?", "onPause: the screen is partly hidden or losing focus. onStop: it's no longer visible at all."),
            ("How does a ViewModel survive rotation?", "It's scoped to the screen's lifecycle owner, not the view instance, so the system keeps it while the screen is recreated."),
            ("How do you avoid memory leaks in mobile apps?", "Don't hold references to screens or contexts in long-lived objects, unregister listeners, and cancel background work when the screen goes away."),
        ],
    },
    "Building UIs (Compose / SwiftUI / Flutter)": {
        "simple": [
            ("Declarative UI", "You describe what the screen should look like for the current data; the framework updates it when data changes."),
            ("State", "When state changes, only the affected parts of the UI redraw (recompose or rebuild)."),
            ("State hoisting", "Keep state in the parent and pass it down, so child components stay simple and reusable."),
            ("Lists", "Use lazy lists (LazyColumn, List, ListView.builder) that only build visible items, even for thousands of rows."),
            ("Theming", "Define colours, fonts and spacing once and reuse them, including dark mode."),
        ],
        "qa": [
            ("What causes unnecessary recompositions?", "Passing new objects or lambdas on every render, or reading state too high in the tree. Remember values and keep state close to where it's used."),
            ("How do you handle navigation?", "Use the framework's navigation library with routes, passing IDs rather than whole objects between screens."),
            ("Flutter vs React Native rendering?", "Flutter draws everything itself with its own engine; React Native uses the platform's native components."),
        ],
    },
    "Networking & APIs": {
        "simple": [
            ("HTTP client", "Libraries like Retrofit, URLSession or Dio send requests and turn JSON responses into objects."),
            ("Background threads", "Network calls must never run on the main thread, or the app freezes."),
            ("Errors", "Handle timeouts, no internet and server errors with clear messages and a retry option."),
            ("Caching", "Show saved data instantly and refresh in the background for a fast, offline-friendly feel."),
            ("Security", "Use HTTPS only and never hard-code secret keys in the app."),
        ],
        "qa": [
            ("How do you handle a slow or flaky network?", "Timeouts, retries with backoff, cached data, optimistic UI updates and clear loading and error states."),
            ("How do you paginate a long feed?", "Request pages with a cursor as the user scrolls near the end, appending results to the list."),
            ("Why can't you keep API secrets in a mobile app?", "Anyone can download and decompile the app to extract them. Keep secrets on your server and call it instead."),
        ],
    },
    "Local Storage & Offline-first": {
        "simple": [
            ("Key-value storage", "Small settings like dark mode on/off go in SharedPreferences or DataStore, or UserDefaults on iOS."),
            ("Local database", "Structured data goes in SQLite through Room or Core Data, and can be searched and sorted."),
            ("Secure storage", "Tokens and passwords go in the Keychain or Keystore, which the OS encrypts."),
            ("Offline-first", "The app reads and writes the local database first and syncs with the server in the background."),
            ("Conflicts", "If the same data changes on two devices, decide a rule: latest edit wins, or merge fields."),
        ],
        "qa": [
            ("How do you sync offline changes?", "Queue local changes (an 'outbox'), send them when online with retries, and resolve conflicts using timestamps or versions."),
            ("Where would you store a user's auth token?", "In the Keychain or Keystore, never in plain preferences or files."),
            ("Why is a local database the 'single source of truth'?", "The UI always reads from one place, so it stays consistent and works offline; the network just updates that database."),
        ],
    },
    "MVVM & Clean Architecture": {
        "simple": [
            ("MVVM", "Model (data), View (screen) and ViewModel (prepares data for the screen and handles user actions)."),
            ("Repository", "One place that decides where data comes from, network or local database, so screens don't care."),
            ("Layers", "UI → domain (business rules) → data. Each layer only talks to the one below it."),
            ("Dependency injection", "Pass dependencies in from outside (Hilt, Koin) instead of creating them inside, which makes testing easy."),
            ("Modules", "Split big apps into feature modules for faster builds and clear ownership."),
        ],
        "qa": [
            ("Why shouldn't a ViewModel hold a reference to a View or Activity?", "The ViewModel outlives the view (for example across rotations), so holding it leaks memory and can crash."),
            ("What goes in a use case or interactor?", "A single business action, like PlaceOrder, combining repositories and rules, independent of UI and frameworks."),
            ("How does this architecture help testing?", "Each layer can be tested alone by injecting fakes, such as testing a ViewModel with a fake repository."),
        ],
    },
    "Testing, Performance & Publishing": {
        "simple": [
            ("Unit tests", "Test ViewModels and business logic quickly on your computer, with fake data sources."),
            ("UI tests", "Espresso, XCTest or Flutter tests tap through screens to check real user flows."),
            ("Profiling", "Use profilers to find slow screens, memory leaks and battery drain before users do."),
            ("Crash reporting", "Tools like Crashlytics show which crashes affect the most users."),
            ("Staged rollout", "Release to 5% of users first, watch for problems, then increase."),
        ],
        "qa": [
            ("How do you reduce app startup time?", "Do less on launch: lazy-load features, defer initialisation, avoid heavy work on the main thread, and use baseline profiles on Android."),
            ("What is ProGuard / R8?", "Tools that shrink, optimise and obfuscate Android code, making the app smaller and harder to reverse-engineer."),
            ("What do you check before publishing an app?", "Signing, versioning, store guidelines and privacy policy, permissions justification, crash-free testing, and release notes."),
        ],
    },
    "CIA Triad, Threats & Risk": {
        "simple": [
            ("Confidentiality", "Only the right people can see the data, protected by encryption and access control."),
            ("Integrity", "Data isn't secretly changed, protected by hashes, signatures and permissions."),
            ("Availability", "Systems are up when needed, protected by backups, redundancy and DDoS protection."),
            ("Risk", "How likely something bad is × how much damage it would cause. Fix the biggest risks first."),
            ("Defence in depth", "Several layers of protection, so if one fails, others still stop the attacker."),
        ],
        "qa": [
            ("What is a threat model?", "A structured look at what you're protecting, who might attack, how (for example using STRIDE), and which defences to prioritise."),
            ("What is least privilege?", "Give every user and service only the access they need, nothing more, which limits damage if they're compromised."),
            ("Vulnerability vs threat vs risk?", "A vulnerability is a weakness, a threat is something that could exploit it, and risk is the likelihood and impact of that happening."),
        ],
    },
    "Cryptography Essentials": {
        "simple": [
            ("Symmetric encryption", "One shared key locks and unlocks (AES). Fast, but both sides need the same secret key."),
            ("Asymmetric encryption", "A public key locks and only the matching private key unlocks (RSA, ECC). Solves sharing keys safely."),
            ("Hashing", "A one-way fingerprint of data (SHA-256). You can't reverse it, but you can check if data changed."),
            ("Digital signatures", "Prove who sent something and that it wasn't altered, by signing with a private key."),
            ("Certificates", "Signed documents from trusted authorities that link a website to its public key."),
        ],
        "qa": [
            ("Why do we salt password hashes?", "A unique random salt per user means identical passwords get different hashes and precomputed 'rainbow tables' don't work."),
            ("Encoding vs encryption vs hashing?", "Encoding (Base64) just changes format with no secret; encryption needs a key to reverse; hashing can't be reversed."),
            ("How does HTTPS use both kinds of encryption?", "Asymmetric cryptography during the handshake to agree on a key, then fast symmetric encryption for the actual data."),
        ],
    },
    "OWASP Top 10": {
        "simple": [
            ("Broken access control", "Users reaching data or actions they shouldn't, like changing an ID in the URL to see someone else's invoice."),
            ("Injection", "User input treated as code, like SQL injection. Prevent it with parameterised queries."),
            ("Cross-site scripting", "Attacker scripts running in other users' browsers. Prevent it by escaping output and using CSP."),
            ("Security misconfiguration", "Default passwords, debug mode in production, open storage buckets."),
            ("Vulnerable components", "Outdated libraries with known holes. Keep dependencies updated and scanned."),
        ],
        "qa": [
            ("How do you prevent IDOR?", "Check on the server that the logged-in user owns or may access every object they request, not just that they're logged in."),
            ("What is SSRF?", "Server-side request forgery: tricking a server into fetching internal URLs (like cloud metadata). Prevent with allowlists and network rules."),
            ("Why is input validation not enough against XSS?", "Data can be safe in one context but dangerous in another; you must escape output for its context (HTML, attribute, JavaScript)."),
        ],
    },
    "Hands-on Web Pentesting": {
        "simple": [
            ("Permission first", "Only test systems you are explicitly allowed to test. Unauthorised testing is illegal."),
            ("Recon", "Map the application: pages, parameters, APIs, technologies used."),
            ("Burp Suite", "An intercepting proxy that lets you see and modify requests between browser and server."),
            ("Test systematically", "Check authentication, sessions, access control, input handling and business logic flaws."),
            ("Report clearly", "Steps to reproduce, impact, evidence and a fix, so developers can act."),
        ],
        "qa": [
            ("Where can you practise legally?", "PortSwigger Web Security Academy, TryHackMe, HackTheBox, OWASP Juice Shop, and bug bounty programs with clear rules."),
            ("How do you rate a vulnerability's severity?", "Consider impact (data exposed, actions possible) and how easy it is to exploit, often using CVSS."),
            ("What is a business logic flaw?", "A bug in how the app's rules work, like applying a discount coupon unlimited times, which scanners usually miss."),
        ],
    },
    "Network Security": {
        "simple": [
            ("Firewall", "Allows or blocks traffic based on rules, like a guard checking IDs at the gate."),
            ("IDS", "An intrusion detection system watches traffic and raises alarms on suspicious patterns."),
            ("IPS", "An intrusion prevention system sits inline and blocks malicious traffic automatically."),
            ("Segmentation", "Split the network into zones so an attacker who gets into one area can't reach everything."),
            ("VPN and Zero Trust", "A VPN creates an encrypted tunnel; Zero Trust goes further and verifies every request regardless of network location."),
        ],
        "qa": [
            ("What is a DMZ?", "A separate network zone for public-facing servers, isolated from the internal network by firewalls."),
            ("Signature vs anomaly detection?", "Signature detection matches known attack patterns (precise but misses new attacks); anomaly detection flags unusual behaviour (catches new attacks but more false alarms)."),
            ("How do you defend against a DDoS attack?", "Use a CDN or DDoS protection service, rate limiting, auto-scaling, and filtering traffic upstream."),
        ],
    },
    "SOC, SIEM & Threat Detection": {
        "simple": [
            ("SOC", "A Security Operations Centre: the team that watches for attacks around the clock and responds."),
            ("SIEM", "Software that collects logs from everywhere and correlates them to spot attacks."),
            ("IOCs", "Indicators of compromise: clues like suspicious IPs, file hashes or domains linked to attacks."),
            ("MITRE ATT&CK", "A catalogue of real attacker techniques, used to build and check detections."),
            ("Triage", "Quickly decide whether an alert is real, how serious it is, and what to do next."),
        ],
        "qa": [
            ("How do you reduce alert fatigue?", "Tune noisy rules, add context (asset value, user), automate enrichment, and prioritise by severity."),
            ("Walk through investigating a suspicious login alert.", "Check the user, location, device and time, compare with normal behaviour, look for related activity, then contain (reset password, revoke sessions) if needed."),
            ("What logs are most valuable for detection?", "Authentication logs, endpoint process logs, DNS and proxy logs, cloud audit logs, and firewall logs."),
        ],
    },
    "Incident Response & Forensics": {
        "simple": [
            ("Preparation", "Plans, contacts, logging and backups ready before anything happens."),
            ("Detection and analysis", "Confirm the incident is real and figure out its scope."),
            ("Containment", "Stop the spread, for example by isolating infected machines, while keeping evidence."),
            ("Eradication and recovery", "Remove the attacker's access, fix the weakness, and restore from clean backups."),
            ("Lessons learned", "Review what happened and improve defences so it doesn't happen again."),
        ],
        "qa": [
            ("Why preserve evidence before cleaning a system?", "Memory and disk evidence show how the attacker got in and what they took; wiping too early destroys it."),
            ("What is chain of custody?", "A record of who handled evidence and when, so it stays trustworthy, which is important if legal action follows."),
            ("Ransomware hits a company. What are the first steps?", "Isolate affected systems, activate the response plan, preserve evidence, assess backups, communicate with stakeholders, and involve legal or authorities as required."),
        ],
    },
}
