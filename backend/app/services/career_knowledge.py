import re
import json
from typing import Dict, Any, List, Tuple

class CareerKnowledgeEngine:
    """
    High-fidelity, comprehensive knowledge and dynamic response engine for
    AI Career & Coding Coach, providing dynamic, technically precise, and actionable answers.
    """

    OUT_OF_SCOPE_MESSAGE = (
        "I am designed only to answer questions related to interview, technical or communication skills only, "
        "so sorry I will not be able to answer this question.\n\n"
        "Please feel free to ask me anything about:\n"
        "- 💻 **Technical & Coding**: Algorithms, data structures, system design, debugging, or code implementations.\n"
        "- 🎯 **Interview Preparation**: Behavioral questions, HR rounds, mock interview answers, and STAR frameworks.\n"
        "- 🗣️ **Communication Skills**: English fluency for interviews, articulation, body language, and placement communication."
    )

    @classmethod
    def is_in_scope(cls, query: str) -> bool:
        """
        Determines whether the query is strictly unrelated to engineering, tech, career, or interviews.
        Permits ALL DSA, technical, coding, CS, and engineering topics/subjects.
        Rejects ONLY purely non-technical/non-career requests like recipes, sports scores, movie gossip, weather, etc.
        """
        q_clean = query.lower().strip()
        if not q_clean:
            return True

        # Purely unrelated everyday topics filter
        out_of_scope_patterns = [
            r'\b(recipe|recipes|how to cook|how to bake|ingredient|ingredients|pasta recipe|pizza recipe|cake recipe|biryani recipe|bake a cake)\b',
            r'\b(cook|bake|fry|boil)\s+(chicken|rice|paneer|curry|meat|fish|soup|pasta|egg|vegetable|mutton|food|meal|dinner|lunch|breakfast)\b',
            r'\b(movie review|movie recommendation|latest movies|box office|who acted in|hollywood gossip|bollywood gossip|song lyrics|download song|bollywood|hollywood)\b',
            r'\b(cricket|football|soccer|ipl|fifa|badminton|tennis|nba|olympics)\b',
            r'\b(weather|forecast today|rain today|temperature outside|weather today|tomorrow weather)\b',
            r'\b(paracetamol|medicine for|tablet for headache|cure disease|medical prescription|doctor prescription)\b',
            r'\b(horoscope today|zodiac sign compatibility|astrology prediction)\b',
            r'\b(how to get a girlfriend|how to get a boyfriend|dating tips|tinder profile tips|girlfriend|boyfriend|dating advice)\b',
            r'\b(politics|election|prime minister|president of|celebrity|actor|actress|netflix|web series|anime|tv show|song|music video|lyrics)\b',
            r'\b(stock tips|crypto price|bitcoin price|lottery|betting|gambling|horoscope|religion|god|tarot)\b',
            r'\b(travel plan|tourist|hotel booking|restaurant|recipe|diet plan|weight loss|workout plan|gym routine|skincare|makeup|fashion)\b',
            r'\b(joke|poem about|write a story|love letter|birthday wish|shayari)\b',
        ]

        # Exceptions where a word overlaps with an engineering/computing context
        tech_overlap = bool(re.search(
            r'\b(engineering|science|math|physics|chemistry|mechanic|mechanical|electric|electrical|electronic|electronics|circuit|thermodynamic|thermodynamics|signal|control|computer|software|hardware|code|coding|algorithm|dsa|hash|map|hashmap|hashtable|hashing|system|design|app|api|program|project|database|developer|interview|placement|study|exam|course|college|career|work|job|skills)\b',
            q_clean
        ))

        for pat in out_of_scope_patterns:
            if re.search(pat, q_clean) and not tech_overlap:
                return False

        # Everything else is in scope: ALL DSA, ALL engineering subjects, career & interview topics!
        return True

    @classmethod
    def get_response(cls, query: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        if not query or not query.strip():
            return {
                "response": "Hello! I am your **GapX AI Career Coach**. Ask me any technical doubt, coding problem (e.g. *'Write Two Sum in Python'*), system design concept, or career question (e.g. *'How to answer Tell me about yourself'*), and I will provide in-depth, actionable guidance.",
                "suggestions": ["Solve Two Sum in Python", "How to prepare for FAANG interviews?", "Explain OOP concepts with code"]
            }

        q = query.strip()
        q_lower = q.lower()

        # Strict Topic Guardrail Check
        if not cls.is_in_scope(q):
            return {
                "response": cls.OUT_OF_SCOPE_MESSAGE,
                "suggestions": [
                    "How to prepare for technical interviews?",
                    "Solve Two Sum in Python",
                    "Tips to improve communication skills for interviews"
                ]
            }

        # Check detected language preference in query
        lang = "python"
        if re.search(r'\b(java\b|in java)', q_lower) and not re.search(r'javascript', q_lower):
            lang = "java"
        elif re.search(r'\b(c\+\+|cpp|in c\+\+)', q_lower):
            lang = "cpp"
        elif re.search(r'\b(javascript|js|in js|in javascript)', q_lower):
            lang = "javascript"
        elif re.search(r'\b(typescript|ts|in ts)', q_lower):
            lang = "typescript"
        elif re.search(r'\b(golang|go|in go)', q_lower):
            lang = "go"
        elif re.search(r'\b(sql|in sql|query)', q_lower):
            lang = "sql"

        # 1. CODING / ALGORITHM PROBLEMS
        code_res = cls._match_coding_problem(q_lower, lang)
        if code_res:
            return code_res

        # 2. SYSTEM DESIGN & TECHNICAL CONCEPTS
        concept_res = cls._match_technical_concept(q_lower)
        if concept_res:
            return concept_res

        # 3. CAREER & INTERVIEW GUIDANCE
        career_res = cls._match_career_question(q_lower)
        if career_res:
            return career_res

        # 4. DYNAMIC NATURAL LANGUAGE RESOLUTION
        return cls._dynamic_generate(q, q_lower, history)

    # ──────────────────────────────────────────────────────────────────────────
    # 1. CODING PROBLEM MATCHERS
    # ──────────────────────────────────────────────────────────────────────────
    @classmethod
    def _match_coding_problem(cls, q: str, lang: str) -> Dict[str, Any]:
        # Two Sum
        if "two sum" in q or "2 sum" in q or ("pair" in q and "target sum" in q):
            codes = {
                "python": '''def two_sum(nums: list[int], target: int) -> list[int]:
    """
    Finds two indices such that nums[i] + nums[j] == target.
    Time Complexity: O(N) | Space Complexity: O(N)
    """
    seen = {}  # maps value -> index
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

# Example Test:
print(two_sum([2, 7, 11, 15], 9))  # Output: [0, 1]''',
                "java": '''import java.util.HashMap;
import java.util.Map;

class Solution {
    public int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> seen = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            int complement = target - nums[i];
            if (seen.containsKey(complement)) {
                return new int[] { seen.get(complement), i };
            }
            seen.put(nums[i], i);
        }
        return new int[0];
    }
}''',
                "cpp": '''#include <vector>
#include <unordered_map>
using namespace std;

class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int> seen;
        for (int i = 0; i < nums.size(); i++) {
            int complement = target - nums[i];
            if (seen.find(complement) != seen.end()) {
                return {seen[complement], i};
            }
            seen[nums[i]] = i;
        }
        return {};
    }
};''',
                "javascript": '''function twoSum(nums, target) {
    const seen = new Map();
    for (let i = 0; i < nums.length; i++) {
        const complement = target - nums[i];
        if (seen.has(complement)) {
            return [seen.get(complement), i];
        }
        seen.set(nums[i], i);
    }
    return [];
}

console.log(twoSum([2, 7, 11, 15], 9)); // [0, 1]'''
            }
            code_block = codes.get(lang, codes["python"])
            response = f"""### 🧩 Two Sum Problem Solution

#### 🎯 Problem Breakdown:
Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.

#### 💡 Optimal Approach (One-Pass Hash Map):
1. Instead of a nested loop checking all pairs in $O(N^2)$, maintain a Hash Map (lookup table).
2. For each number $x$, compute the required complement: $\\text{{complement}} = \\text{{target}} - x$.
3. Check if $\\text{{complement}}$ is already in the map:
   - **If yes**: Return `[seen[complement], current_index]`.
   - **If no**: Insert `x -> current_index` into the map and continue.

#### 💻 Clean Implementation ({lang.capitalize()}):
```{lang}
{code_block}
```

#### ⏱️ Complexity Analysis:
- **Time Complexity**: $\\mathcal{{O}}(N)$ — We traverse the list of length $N$ exactly once. Hash map lookups and insertions take $\\mathcal{{O}}(1)$ average time.
- **Space Complexity**: $\\mathcal{{O}}(N)$ — Auxiliary storage for storing up to $N$ elements in the hash map.

#### ⚠️ Edge Cases & Interview Follow-ups:
- Negative integers (e.g. `[-3, 4, 3, 90]`, target `0` $\\to$ `[0, 2]`).
- Duplicates (e.g. `[3, 3]`, target `6` $\\to$ `[0, 1]`).
- What if the input array is sorted? $\\implies$ Use **Two Pointers** for $\\mathcal{{O}}(1)$ space!
"""
            return {
                "response": response,
                "suggestions": ["Show Two Sum using Two Pointers (Sorted Array)", "Solve 3Sum problem in Python", "Explain Hash Map collision resolution"]
            }

        # Reverse Linked List
        if "reverse" in q and ("linked list" in q or "link list" in q or "singly" in q):
            codes = {
                "python": '''class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def reverse_list_iterative(head: ListNode) -> ListNode:
    """
    Reverses a singly linked list iteratively.
    Time: O(N) | Space: O(1)
    """
    prev = None
    curr = head
    while curr:
        nxt = curr.next  # Save next node
        curr.next = prev  # Reverse pointer
        prev = curr       # Move prev forward
        curr = nxt        # Move curr forward
    return prev

def reverse_list_recursive(head: ListNode) -> ListNode:
    """
    Reverses a singly linked list recursively.
    Time: O(N) | Space: O(N) call stack
    """
    if not head or not head.next:
        return head
    new_head = reverse_list_recursive(head.next)
    head.next.next = head
    head.next = None
    return new_head''',
                "java": '''class ListNode {
    int val;
    ListNode next;
    ListNode(int val) { this.val = val; }
}

class Solution {
    public ListNode reverseList(ListNode head) {
        ListNode prev = null;
        ListNode curr = head;
        while (curr != null) {
            ListNode nextTemp = curr.next;
            curr.next = prev;
            prev = curr;
            curr = nextTemp;
        }
        return prev;
    }
}''',
                "cpp": '''struct ListNode {
    int val;
    ListNode *next;
    ListNode(int x) : val(x), next(nullptr) {}
};

class Solution {
public:
    ListNode* reverseList(ListNode* head) {
        ListNode* prev = nullptr;
        ListNode* curr = head;
        while (curr != nullptr) {
            ListNode* nxt = curr->next;
            curr->next = prev;
            prev = curr;
            curr = nxt;
        }
        return prev;
    }
};'''
            }
            code_block = codes.get(lang, codes["python"])
            response = f"""### 🔗 Reverse a Singly Linked List

#### 🎯 Problem Overview:
Given the `head` of a singly linked list, reverse the list and return the reversed list's head.

#### 💡 Optimal Approach (Three Pointers):
Use three pointers: `prev` (initialized to `None`/`nullptr`), `curr` (initialized to `head`), and `nxt` (temporary holder).
1. Store `curr.next` in `nxt`.
2. Repoint `curr.next` to `prev`.
3. Advance `prev = curr` and `curr = nxt`.
4. Return `prev` when `curr` becomes null.

#### 💻 Production Implementation ({lang.capitalize()}):
```{lang}
{code_block}
```

#### ⏱️ Complexity Analysis:
- **Time Complexity**: $\\mathcal{{O}}(N)$ where $N$ is the number of nodes in the linked list.
- **Space Complexity**: $\\mathcal{{O}}(1)$ for the iterative approach; $\\mathcal{{O}}(N)$ auxiliary stack space for recursion.

#### ⚠️ Critical Edge Cases:
- Empty list (`head == None`).
- Single-node list (`head.next == None`).
- Cycle detection (what if the linked list has a loop? Use **Floyd's Tortoise and Hare algorithm**).
"""
            return {
                "response": response,
                "suggestions": ["How to detect a cycle in a Linked List?", "Reverse Linked List II (between m and n)", "Merge two sorted linked lists"]
            }

        # Binary Search
        if "binary search" in q or ("search" in q and "sorted array" in q):
            codes = {
                "python": '''def binary_search(arr: list[int], target: int) -> int:
    """
    Standard Binary Search algorithm on sorted array.
    Time Complexity: O(log N) | Space Complexity: O(1)
    """
    low = 0
    high = len(arr) - 1
    
    while low <= high:
        # Prevents integer overflow: low + (high - low) // 2
        mid = low + (high - low) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
            
    return -1  # Target not found

# Test:
print(binary_search([-1, 0, 3, 5, 9, 12], 9))  # Output: 4''',
                "java": '''class Solution {
    public int search(int[] nums, int target) {
        int low = 0, high = nums.length - 1;
        while (low <= high) {
            int mid = low + (high - low) / 2; // Prevents overflow
            if (nums[mid] == target) return mid;
            else if (nums[mid] < target) low = mid + 1;
            else high = mid - 1;
        }
        return -1;
    }
}''',
                "cpp": '''class Solution {
public:
    int search(vector<int>& nums, int target) {
        int low = 0, high = nums.size() - 1;
        while (low <= high) {
            int mid = low + (high - low) / 2;
            if (nums[mid] == target) return mid;
            else if (nums[mid] < target) low = mid + 1;
            else high = mid - 1;
        }
        return -1;
    }
};'''
            }
            code_block = codes.get(lang, codes["python"])
            response = f"""### 🔍 Binary Search Algorithm

#### 🎯 Problem Overview:
Given a sorted array of integers `arr` and a `target` value, return its index in $\\mathcal{{O}}(\\log N)$ time.

#### 💡 Core Mechanism:
1. Initialize two pointers: `low = 0` and `high = len(arr) - 1`.
2. Compute `mid = low + (high - low) // 2` (avoids 32-bit integer overflow in languages like C++/Java).
3. If `arr[mid] == target`, target is found.
4. If `arr[mid] < target`, discard the left half by setting `low = mid + 1`.
5. If `arr[mid] > target`, discard the right half by setting `high = mid - 1`.

#### 💻 Clean Implementation ({lang.capitalize()}):
```{lang}
{code_block}
```

#### ⏱️ Complexity Analysis:
- **Time Complexity**: $\\mathcal{{O}}(\\log N)$ — The search space is halved on every iteration ($N \\to N/2 \\to N/4 \\to \\dots \\to 1$).
- **Space Complexity**: $\\mathcal{{O}}(1)$ auxiliary memory.

#### 🚀 FAANG Variants:
- Search in Rotated Sorted Array (LeetCode 33)
- Find First and Last Position of Element in Sorted Array (LeetCode 34)
- Capacity To Ship Packages Within D Days (Binary Search on Answer Space)
"""
            return {
                "response": response,
                "suggestions": ["Search in Rotated Sorted Array code", "Binary search on answer space explanation", "Find first and last occurrence in sorted array"]
            }

        # Valid Parentheses / Stack
        if "valid parentheses" in q or ("parentheses" in q and "stack" in q) or "matching bracket" in q:
            codes = {
                "python": '''def is_valid_parentheses(s: str) -> bool:
    """
    Verifies valid matching brackets: '()', '{}', '[]'
    Time: O(N) | Space: O(N)
    """
    bracket_map = {')': '(', '}': '{', ']': '['}
    stack = []
    
    for char in s:
        if char in bracket_map:
            top_element = stack.pop() if stack else '#'
            if bracket_map[char] != top_element:
                return False
        else:
            stack.append(char)
            
    return len(stack) == 0

# Test Cases:
print(is_valid_parentheses("()[]{}"))  # True
print(is_valid_parentheses("(]"))      # False''',
                "java": '''import java.util.Stack;

class Solution {
    public boolean isValid(String s) {
        Stack<Character> stack = new Stack<>();
        for (char c : s.toCharArray()) {
            if (c == '(') stack.push(')');
            else if (c == '{') stack.push('}');
            else if (c == '[') stack.push(']');
            else if (stack.isEmpty() || stack.pop() != c) return false;
        }
        return stack.isEmpty();
    }
}'''
            }
            code_block = codes.get(lang, codes["python"])
            response = f"""### 🧱 Valid Parentheses (Stack)

#### 🎯 Problem Overview:
Given a string `s` containing `'(', ')', '{', '}', '[', ']'`, determine if the input string is valid.

#### 💡 Approach (LIFO Stack):
- As we iterate through each character, push opening brackets onto the stack.
- When an incoming closing bracket appears, pop the top of the stack and check for a match.
- If the stack is empty when a closing bracket appears or the popped character doesn't match, return `False`.
- After processing, the stack must be completely empty.

#### 💻 Implementation ({lang.capitalize()}):
```{lang}
{code_block}
```

#### ⏱️ Complexity:
- **Time Complexity**: $\\mathcal{{O}}(N)$
- **Space Complexity**: $\\mathcal{{O}}(N)$ in worst case where all characters are opening brackets.
"""
            return {
                "response": response,
                "suggestions": ["Min Stack implementation in Python", "Evaluate Reverse Polish Notation", "Daily Temperatures Monotonic Stack"]
            }

        # Maximum Subarray / Kadane's Algorithm
        if "kadane" in q or "max subarray" in q or "maximum subarray" in q or "largest sum subarray" in q:
            response = f"""### ⚡ Maximum Subarray (Kadane's Algorithm)

#### 🎯 Problem:
Find the contiguous subarray with the largest sum and return its sum.

#### 💡 Core Intuition:
At every index `i`, we make a local greedy choice:
$$\\text{{current\\_sum}} = \\max(\\text{{nums}}[i], \\text{{current\\_sum}} + \\text{{nums}}[i])$$
If adding the previous accumulated sum makes the result worse than starting fresh at `nums[i]`, start a new subarray.

#### 💻 Implementation ({lang.capitalize()}):
```{lang}
def max_sub_array(nums: list[int]) -> int:
    # Kadane's Algorithm. Time: O(N) | Space: O(1)
    max_so_far = nums[0]
    current_sum = nums[0]
    
    for num in nums[1:]:
        current_sum = max(num, current_sum + num)
        max_so_far = max(max_so_far, current_sum)
        
    return max_so_far

# Test:
print(max_sub_array([-2, 1, -3, 4, -1, 2, 1, -5, 4]))  # Output: 6 ([4, -1, 2, 1])
```

#### ⏱️ Complexity:
- **Time**: $\\mathcal{{O}}(N)$ single pass.
- **Space**: $\\mathcal{{O}}(1)$ constant memory.
"""
            return {
                "response": response,
                "suggestions": ["Print the actual subarray indices in Kadane's", "Maximum Product Subarray", "Trapping Rain Water algorithm"]
            }

        # LRU Cache
        if "lru cache" in q or "lru" in q or "least recently used" in q:
            response = """### 💾 LRU (Least Recently Used) Cache Design

#### 🎯 Architecture Design:
An LRU Cache requires $\\mathcal{O}(1)$ time complexity for both `get(key)` and `put(key, value)`.
- **Hash Map**: Provides $\\mathcal{O}(1)$ key-to-node lookups.
- **Doubly Linked List (DLL)**: Provides $\\mathcal{O}(1)$ node removal and insertion at the head (Most Recently Used) and eviction at the tail (Least Recently Used).

#### 💻 Production Implementation in Python:
```python
class Node:
    def __init__(self, key=0, val=0):
        self.key = key
        self.val = val
        self.prev = None
        self.next = None

class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.cache = {}  # key -> Node
        # Dummy head and tail to eliminate null checks
        self.head = Node()
        self.tail = Node()
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node: Node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_to_front(self, node: Node):
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        if key in self.cache:
            node = self.cache[key]
            self._remove(node)
            self._add_to_front(node)  # Mark as MRU
            return node.val
        return -1

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self._remove(self.cache[key])
        node = Node(key, value)
        self.cache[key] = node
        self._add_to_front(node)
        
        if len(self.cache) > self.cap:
            # Evict from tail (LRU)
            lru = self.tail.prev
            self._remove(lru)
            del self.cache[lru.key]
```

#### ⏱️ Complexity:
- **`get`**: $\\mathcal{O}(1)$
- **`put`**: $\\mathcal{O}(1)$
- **Space**: $\\mathcal{O}(\\text{capacity})$
"""
            return {
                "response": response,
                "suggestions": ["LFU Cache design vs LRU", "Explain Cache Invalidation Strategies", "System Design: Distributed Cache with Redis"]
            }

        # SQL Queries (Second Highest Salary / Joins / Window functions)
        if "sql" in q and ("salary" in q or "highest" in q or "query" in q or "join" in q or "window" in q):
            response = """### 🗄️ Essential SQL Placement Queries

#### 1. Find 2nd Highest Salary (Handling Duplicates & NULLs):
```sql
-- Method 1: Using DENSE_RANK() (Standard in Tech Interviews)
WITH RankedSalaries AS (
    SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) as rank_pos
    FROM Employee
)
SELECT salary AS SecondHighestSalary
FROM RankedSalaries
WHERE rank_pos = 2
LIMIT 1;

-- Method 2: Using Subquery (Universal SQL)
SELECT MAX(salary) AS SecondHighestSalary
FROM Employee
WHERE salary < (SELECT MAX(salary) FROM Employee);
```

#### 2. Employees Earning More Than Their Managers:
```sql
SELECT e.name AS Employee
FROM Employee e
JOIN Employee m ON e.managerId = m.id
WHERE e.salary > m.salary;
```

#### 3. Top 3 Salaries per Department (Window Function):
```sql
WITH DeptRanks AS (
    SELECT 
        d.name AS Department,
        e.name AS Employee,
        e.salary AS Salary,
        DENSE_RANK() OVER (PARTITION BY e.departmentId ORDER BY e.salary DESC) AS rnk
    FROM Employee e
    JOIN Department d ON e.departmentId = d.id
)
SELECT Department, Employee, Salary
FROM DeptRanks
WHERE rnk <= 3;
```
"""
            return {
                "response": response,
                "suggestions": ["Explain SQL Indexing B-Trees", "Difference between INNER JOIN and LEFT JOIN", "ACID properties in DBMS"]
            }

        return None

    # ──────────────────────────────────────────────────────────────────────────
    # 2. SYSTEM DESIGN & TECHNICAL CONCEPTS
    # ──────────────────────────────────────────────────────────────────────────
    @classmethod
    def _match_technical_concept(cls, q: str) -> Dict[str, Any]:
        # Hash Map / Hash Table / Hashing
        if any(term in q for term in ["hashmap", "hash map", "hashtable", "hash table", "hashing", "separate chaining", "open addressing"]):
            response = """### ⚡ Hash Map (Hash Table) Deep Dive & Architecture

A **Hash Map** (or Hash Table) is an associative data structure that maps keys to values, achieving **$\\mathcal{O}(1)$ average time complexity** for insertions, lookups, and deletions.

---

#### 🧩 1. Internal Working Mechanism
1. **Hash Function $h(\\text{key})$**: Computes an integer hash code from the key. A good hash function is deterministic and distributes keys uniformly.
2. **Index Compression**: The array index is calculated using modulo:
   $$\\text{index} = h(\\text{key}) \\pmod{\\text{capacity}}$$
   *(In Java / Python power-of-two arrays, this is optimized to bitwise AND: `hash & (capacity - 1)`)*.
3. **Bucket Array**: An internal array of contiguous memory slots. Each slot points to an entry, a linked list, or a balanced tree.
4. **Load Factor ($\\alpha$) & Dynamic Resizing (Rehashing)**:
   $$\\alpha = \\frac{\\text{Number of Stored Entries } (N)}{\\text{Total Capacity } (K)}$$
   - Standard threshold is **0.75** (e.g. Java's `java.util.HashMap`).
   - When $\\alpha > 0.75$, the table **doubles its capacity** and **rehashes** all existing keys into the new array. This amortizes insertions to $\\mathcal{O}(1)$.

---

#### ⚔️ 2. Collision Resolution Techniques

When two distinct keys produce the same bucket index ($h(k_1) \\equiv h(k_2)$), a collision occurs:

##### A. Separate Chaining (Open Hashing)
- Each bucket stores a linked list of entries that collided.
- **Java 8+ Optimization**: When a bucket's linked list length reaches **8 (TREEIFY_THRESHOLD)** and the table capacity is $\\ge 64$, the linked list converts into a **Red-Black Tree** (Self-Balancing BST). This changes worst-case lookup from $\\mathcal{O}(N)$ down to $\\mathcal{O}(\\log N)$!

##### B. Open Addressing (Closed Hashing)
All elements reside directly within the array itself. When a collision occurs, the algorithm probes alternative slots:
- **Linear Probing**: $h(k, i) = (h'(k) + i) \\pmod m$. Fast cache locality, but vulnerable to **primary clustering** (long contiguous blocks of occupied cells).
- **Quadratic Probing**: $h(k, i) = (h'(k) + c_1 i + c_2 i^2) \\pmod m$. Alleviates primary clustering.
- **Double Hashing**: $h(k, i) = (h_1(k) + i \\cdot h_2(k)) \\pmod m$. Uses a secondary hash function for probe step size; provides the best uniform spread among open addressing methods.

---

#### ⏱️ 3. Time & Space Complexity

| Operation | Average Case | Worst Case (All Collide) | Java 8+ Treeified Worst Case |
| :--- | :--- | :--- | :--- |
| **Search / Get** | $\\mathcal{O}(1)$ | $\\mathcal{O}(N)$ | $\\mathcal{O}(\\log N)$ |
| **Insert / Put** | $\\mathcal{O}(1)$ amortized | $\\mathcal{O}(N)$ | $\\mathcal{O}(\\log N)$ |
| **Delete / Remove** | $\\mathcal{O}(1)$ | $\\mathcal{O}(N)$ | $\\mathcal{O}(\\log N)$ |
| **Space Complexity** | $\\mathcal{O}(N)$ | $\\mathcal{O}(N)$ | $\\mathcal{O}(N)$ |

---

#### 💻 4. Code Implementation Examples

##### Python (`dict` & Custom Separate Chaining):
```python
# Custom Hash Map with Separate Chaining
class HashMap:
    def __init__(self, capacity: int = 16):
        self.capacity = capacity
        self.size = 0
        self.buckets = [[] for _ in range(capacity)]

    def _hash(self, key) -> int:
        return hash(key) % self.capacity

    def put(self, key, value) -> None:
        index = self._hash(key)
        bucket = self.buckets[index]
        for i, (k, v) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)  # Update existing
                return
        bucket.append((key, value))
        self.size += 1

    def get(self, key):
        index = self._hash(key)
        for k, v in self.buckets[index]:
            if k == key:
                return v
        return None  # Key not found
```

##### Java (`HashMap`):
```java
import java.util.HashMap;
import java.util.Map;

public class Main {
    public static void main(String[] args) {
        Map<String, Integer> map = new HashMap<>();
        map.put("Apple", 5);
        map.put("Banana", 3);
        System.out.println("Apple count: " + map.getOrDefault("Apple", 0)); // 5
    }
}
```

##### C++ (`std::unordered_map`):
```cpp
#include <iostream>
#include <unordered_map>
#include <string>

int main() {
    std::unordered_map<std::string, int> freq;
    freq["placement"] = 100;
    if (freq.find("placement") != freq.end()) {
        std::cout << "Found: " << freq["placement"] << "\\n";
    }
    return 0;
}
```

---

#### 🏆 5. Top LeetCode & Interview Patterns
1. **Two Sum**: Complements lookup in single pass $\\mathcal{O}(N)$.
2. **Group Anagrams**: Use sorted word or 26-char frequency tuple as the map key.
3. **Longest Consecutive Sequence**: Use `HashSet` for $\\mathcal{O}(1)$ neighbor lookups.
4. **Subarray Sum Equals K**: Cumulative prefix sum frequency hash map.
5. **LRU Cache**: Doubly Linked List + HashMap for $\\mathcal{O}(1)$ get and evict.
"""
            return {
                "response": response,
                "suggestions": [
                    "How does Java 8 HashMap Red-Black tree conversion work?",
                    "Difference between HashMap and HashTable / ConcurrentHashMap",
                    "Solve Group Anagrams using HashMap in Python"
                ]
            }

        # OOP Concepts
        if "oop" in q or "object oriented" in q or "encapsulation" in q or "polymorphism" in q:
            response = """### 🏛️ Object-Oriented Programming (OOP) Core Pillars

OOP structures software into modular, reusable blueprints (classes) and instances (objects).

#### The 4 Core Pillars:

1. **Encapsulation**:
   - Bundling data (state) and methods (behavior) within a single unit, hiding internal state from unauthorized outside mutation (`private`/`protected` fields).
   ```python
   class BankAccount:
       def __init__(self, balance: float):
           self.__balance = balance  # Private attribute

       def deposit(self, amount: float):
           if amount > 0:
               self.__balance += amount

       def get_balance(self) -> float:
           return self.__balance
   ```

2. **Abstraction**:
   - Hiding complex implementation mechanics and exposing only clear interfaces to the user (e.g. `car.accelerate()` without needing to know engine fuel-injection mechanics).
   ```python
   from abc import ABC, abstractmethod

   class PaymentGateway(ABC):
       @abstractmethod
       def process_payment(self, amount: float) -> bool:
           pass
   ```

3. **Inheritance**:
   - Creating new classes that reuse, extend, and specialize the behavior of existing parent classes (`class Dog(Animal)`), reducing code duplication.

4. **Polymorphism** (*"Many Forms"*):
   - **Method Overriding (Runtime Polymorphism)**: Subclass provides a specific implementation of a parent class method.
   - **Method Overloading (Compile-time Polymorphism)**: Same method name with different signatures/parameters.

#### 💡 SOLID Principles Quick Reference:
- **S**: Single Responsibility Principle
- **O**: Open/Closed Principle (Open for extension, closed for modification)
- **L**: Liskov Substitution Principle
- **I**: Interface Segregation Principle
- **D**: Dependency Inversion Principle
"""
            return {
                "response": response,
                "suggestions": ["Explain SOLID principles with code", "Composition vs Inheritance", "Design Patterns: Factory vs Singleton"]
            }

        # REST API vs GraphQL
        if ("rest" in q and "graphql" in q) or "rest vs" in q or "api design" in q or "graphql vs" in q:
            response = """### 🌐 REST API vs GraphQL Comparison

| Feature | **REST (Representational State Transfer)** | **GraphQL** |
| :--- | :--- | :--- |
| **Architecture** | Resource-driven with multiple HTTP endpoints (`/users`, `/posts`) | Query-driven with a single endpoint (`/graphql`) |
| **Data Fetching** | Fixed payloads; vulnerable to **Over-fetching** & **Under-fetching** | Client requests exact JSON fields required |
| **Network Roundtrips** | Multiple network requests for related entities | Single request fetches nested relationships |
| **HTTP Caching** | Native HTTP/CDN caching via standard headers (`E-Tag`, `Cache-Control`) | Complex caching (requires Relay/Apollo client-side caches) |
| **Protocol** | Standard HTTP verbs (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`) | POST requests with query/mutation schema syntax |

#### When to use which?
- **Choose REST**: Public APIs, simple CRUD services, high-throughput microservices relying on CDN caching.
- **Choose GraphQL**: Mobile apps on constrained bandwidth, complex nested relational dashboards, rapid frontend iterations.
"""
            return {
                "response": response,
                "suggestions": ["How to implement JWT Auth in REST API?", "Explain WebSockets vs Server-Sent Events", "Microservices communication: REST vs gRPC"]
            }

        # Microservices vs Monolith
        if "microservice" in q or "monolith" in q:
            response = """### 🏗️ Microservices vs Monolithic Architecture

#### 1. Monolithic Architecture:
- **Structure**: Entire application (UI, Business Logic, Database Access) packaged as a single unified codebase and deployment binary.
- **Pros**: Easy to develop, test, debug, and deploy initially; zero network latency between modules.
- **Cons**: Single point of failure; difficult to scale independent components; tight code coupling.

#### 2. Microservices Architecture:
- **Structure**: Application split into autonomous, decoupled services communicating via lightweight protocols (REST, gRPC, Kafka).
- **Pros**: Independent deployability & scalability; technology-stack agnostic; isolated blast radius for failures.
- **Cons**: Distributed transactions complexity (need Saga pattern); network latency; complex DevOps orchestration (Kubernetes, Service Mesh).

#### 🚀 Key Patterns in Microservices:
- **API Gateway**: Reverse proxy handling auth, SSL termination, and rate-limiting.
- **Circuit Breaker**: Prevents cascading system failures (e.g. Resilience4j, Netflix Hystrix).
- **Database per Service**: Each service owns its private database.
"""
            return {
                "response": response,
                "suggestions": ["Explain Event-Driven Architecture with Kafka", "How does API Gateway work?", "CAP Theorem explained"]
            }

        # Database Indexing & Caching
        if "index" in q and ("database" in q or "sql" in q or "b-tree" in q or "db" in q):
            response = """### ⚡ Database Indexing & B-Trees Explained

#### 🎯 What is an Index?
A database index is an auxiliary data structure that improves the speed of data retrieval operations on a database table at the cost of additional storage and slower writes (`INSERT`/`UPDATE`/`DELETE`).

#### 🌲 How B-Trees / B+ Trees Work:
1. **Balanced Search Trees**: Keep data sorted with logarithmic search time $\\mathcal{O}(\\log N)$.
2. **High Fanout**: Each node stores hundreds of keys and child pointers, minimizing disk I/O operations.
3. **B+ Tree leaf nodes**: Connected via a doubly linked list, enabling extremely fast **range queries** (`WHERE age BETWEEN 20 AND 30`).

#### 💡 Best Practices:
- Index columns frequently used in `WHERE`, `JOIN`, and `ORDER BY` clauses.
- Use **Composite Indexes** carefully (left-most prefix rule applies).
- Avoid indexing low-cardinality columns (e.g. `gender` with only 2 distinct values).
"""
            return {
                "response": response,
                "suggestions": ["Explain Redis Caching Strategies", "Database Sharding vs Partitioning", "ACID Transactions and Isolation Levels"]
            }

        # Docker & Containers
        if "docker" in q or "container" in q or "kubernetes" in q or "k8s" in q:
            response = """### 🐳 Docker & Containerization Deep Dive

#### 🎯 Why Docker?
Docker packages an application and all its dependencies, runtime libraries, and environment configs into a standardized container image that runs identically on local machines, staging, and production.

#### 📦 Container vs Virtual Machine (VM):
- **Virtual Machines**: Virtualize physical hardware with a Hypervisor; each VM runs a full guest OS (heavyweight: gigabytes, slow startup).
- **Docker Containers**: Virtualize at the OS kernel level (using Linux namespaces and cgroups); share the host OS kernel (lightweight: megabytes, sub-second startup).

#### 📝 Production Dockerfile Example (FastAPI/Python):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Optimize build caching by copying dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
"""
            return {
                "response": response,
                "suggestions": ["Explain CI/CD Pipeline stages with GitHub Actions", "Kubernetes Pods vs Deployments", "Docker Compose multi-container setup"]
            }

        # Operating System Concepts (Processes vs Threads, Deadlocks)
        if "process" in q and "thread" in q:
            response = """### ⚙️ Processes vs Threads in Operating Systems

| Feature | **Process** | **Thread** |
| :--- | :--- | :--- |
| **Definition** | An independent executing program instance | The smallest unit of execution inside a process |
| **Memory Isolation** | Isolated virtual address space (Code, Data, Heap, Stack) | Shares Heap, Code, and Global Data with sibling threads; has private Stack |
| **Creation Overhead** | Heavyweight; involves copying address space (`fork()`) | Lightweight; minimal memory allocation |
| **Communication** | Requires Inter-Process Communication (IPC: Pipes, Sockets, Shared Memory) | Directly accesses shared heap variables (requires synchronization locks) |
| **Crash Impact** | If one process crashes, others are unaffected | If an unhandled thread crashes, the entire parent process can crash |

#### ⚠️ Synchronization Primitives:
- **Mutex**: Mutual exclusion lock (only 1 thread can enter critical section).
- **Semaphore**: Signaling mechanism with a counter (allows $K$ concurrent threads).
"""
            return {
                "response": response,
                "suggestions": ["Explain Deadlocks and 4 Coffman Conditions", "CPU Scheduling: Round Robin vs Priority", "Virtual Memory & Page Faults"]
            }

        return None

    # ──────────────────────────────────────────────────────────────────────────
    # 3. CAREER & INTERVIEW STRATEGY MATCHERS
    # ──────────────────────────────────────────────────────────────────────────
    @classmethod
    def _match_career_question(cls, q: str) -> Dict[str, Any]:
        # "Tell me about yourself"
        if "tell me about yourself" in q or "introduce yourself" in q or "self introduction" in q:
            response = """### 🎤 Mastering "Tell Me About Yourself"

This is your 90-second elevator pitch that sets the tone for the entire interview.

#### 📐 The 4-Part Winning Formula:
1. **Present (30s)**: Who you are, your current role/degree, and your core technical focus.
2. **Past (30s)**: Key projects, internships, or achievements that demonstrate your engineering capabilities.
3. **Future & Company Alignment (30s)**: Why you are passionate about this specific company and role.

---

#### 📝 Concrete Script Example (Fresher / College Graduate):
> *"Hi, I'm [Your Name], a final-year Computer Science student at [University Name]. Over the last two years, I've focused deeply on full-stack development and distributed systems using Python, React, and FastAPI.*
> 
> *Recently, I built [Project Name], an AI-driven platform that handles automated document processing with Redis caching, which achieved a 45% reduction in query latency. I also interned at [Company/Lab], where I developed scalable REST microservices.*
> 
> *I'm particularly excited about [Company Name] because of your work on [Specific Product/Initiative], and I'm eager to bring my problem-solving skills and technical foundation to your engineering team."*

#### 🚫 Common Mistakes to Avoid:
- Reciting your high school history or full resume chronologically.
- Speaking for longer than 2 minutes.
- Being generic without mentioning specific technologies or project achievements.
"""
            return {
                "response": response,
                "suggestions": ["How to answer 'Why should we hire you?'", "How to answer 'What is your biggest weakness?'", "Behavioral interview STAR method"]
            }

        # "Why should we hire you?"
        if "why should we hire you" in q or "why hire you" in q:
            response = """### 🏆 Answering "Why Should We Hire You?"

#### 📐 The 3-Pillar Response Structure:
1. **Technical Competence**: Match your hard skills directly to the job description.
2. **Track Record of Execution**: Mention a tangible project or problem you solved quickly.
3. **Enthusiasm & Culture Fit**: Show genuine curiosity about their engineering culture.

#### 📝 Sample Response:
> *"You should hire me because I offer a strong combination of core computer science fundamentals and hands-on production experience. In my recent work with [Tech Stack], I didn't just write code—I focused on clean architecture, writing unit tests, and optimizing database queries.*
>
> *Beyond technical skills, I am a self-starter who thrives in fast-paced collaborative environments. I'm ready to hit the ground running and add immediate value to your sprint deliverables."*
"""
            return {
                "response": response,
                "suggestions": ["What are your weaknesses interview question", "Behavioral questions STAR method", "Questions to ask the interviewer at the end"]
            }

        # "What is your biggest weakness?"
        if "weakness" in q or "biggest weakness" in q:
            response = """### 🛡️ Answering "What is Your Biggest Weakness?"

#### 💡 The Secret:
Interviewers are testing **self-awareness**, **honesty**, and your **active system for improvement**. Never say *"I'm a perfectionist"* or *"I work too hard"*.

#### 📐 The Formula:
**Real, non-fatal weakness $\\to$ Self-awareness moment $\\to$ Active system/tool you use to overcome it $\\to$ Tangible positive result.**

#### 📝 Sample Answer:
> *"Earlier in my projects, I had a tendency to dive straight into coding before fully scoping out edge cases and architectural diagrams, which sometimes led to refactoring delays.*
> 
> *To fix this, I adopted a strict design-first rule: before writing code, I write a 1-page technical spec and flowchart outlining API contracts, database schemas, and edge scenarios. This has improved my delivery speed and reduced bug counts significantly."*
"""
            return {
                "response": response,
                "suggestions": ["Tell me about a time you failed (STAR)", "How to negotiate salary?", "How to prepare for FAANG coding rounds?"]
            }

        # Behavioral Questions & STAR Method
        if "star method" in q or "behavioral" in q or "situational" in q or "hr interview" in q:
            response = """### 🌟 The STAR Method for Behavioral Interviews

Top tech companies (Amazon Leadership Principles, Google Googlyness, Meta) evaluate candidates using the **STAR Method**:

| Component | Goal | Allocation |
| :--- | :--- | :--- |
| **S - Situation** | Set the context (Company, team, problem scenario). | 15% of time |
| **T - Task** | Describe the specific challenge or objective assigned to you. | 15% of time |
| **A - Action** | Explain the exact technical & leadership steps **YOU** took. | 50% of time |
| **R - Result** | Quantify the positive outcome and what you learned. | 20% of time |

#### 📝 High-Impact Example: *"Tell me about a time you handled a tight deadline."*
- **Situation**: During a 48-hour hackathon, our payment integration API broke due to a breaking schema update from the third-party provider.
- **Task**: As backend lead, I had to fix transactions before the live judging panel.
- **Action**: I isolated the error using request logs, implemented an adapter pattern layer to normalize payloads, and set up fallback mock responses.
- **Result**: Successfully processed all 120 demo checkout transactions without errors and our team secured 2nd place.
"""
            return {
                "response": response,
                "suggestions": ["Top 10 Amazon Leadership Principle questions", "How to prepare for System Design interviews", "Questions to ask the interviewer"]
            }

        # Salary Negotiation
        if "salary" in q or "negotiate" in q or "compensation" in q or "offer" in q:
            response = """### 💰 Software Engineer Salary Negotiation Strategy

#### 🔑 Core Rules:
1. **Never state a number first**: Let the recruiter share the band (*"I'd love to understand the compensation range for this role based on market benchmarks"*).
2. **Evaluate Total Compensation (CTC)**:
   - **Base Salary**: Guaranteed monthly pay (most important for freshers).
   - **Performance Bonus / Variable**: Annual percentage.
   - **Equity / ESOPs / RSUs**: Vesting schedule (e.g. 4-year vest with 1-year cliff).
   - **Joining / Relocation Bonus**: One-time cash payment (easiest component for HR to increase!).
3. **Use Leverage Professionally**: Competing offers, verified market data (Levels.fyi), or unique specialized skill match.

#### 📝 Counter-Offer Email Script:
> *"Thank you so much for the offer! I am genuinely thrilled about the opportunity to join the team and contribute to [Product Name].*
> 
> *Based on my technical background in [Key Skill] and market standards for this position, I was hoping for a base salary closer to [Target Number, +10-15%]. If we can get closer to this figure, I would be excited to sign immediately."*
"""
            return {
                "response": response,
                "suggestions": ["How to evaluate ESOPs vs Cash?", "How to get interview referrals on LinkedIn?", "Resume formatting for ATS"]
            }

        # FAANG / Placement Prep Roadmap
        if "faang" in q or "placement prep" in q or "prepare for interview" in q or "roadmap" in q or "timeline" in q:
            response = """### 🚀 Tier-1 Tech & FAANG Placement Preparation Blueprint

#### 📅 3-Phase Strategy:

```
[Phase 1: DSA Foundations (Weeks 1-6)]
  ├── Arrays, Strings, Hash Maps, Two Pointers, Sliding Window
  ├── Linked Lists, Stacks, Queues, Binary Trees & BSTs
  └── Graphs (BFS/DFS), Dynamic Programming Patterns
      └── Target: Solve 75-100 Curated LeetCode Mediums

[Phase 2: Core CS & System Design (Weeks 7-10)]
  ├── Operating Systems (Process, Threads, Deadlocks)
  ├── Computer Networks (TCP/IP, HTTP/HTTPS, DNS)
  ├── DBMS & SQL (Indexing, ACID, Normalization, Query Tuning)
  └── System Design (Caching, Load Balancers, Sharding, Microservices)

[Phase 3: Projects & Mock Interviews (Weeks 11-14)]
  ├── Build 2 Full-Stack Production Projects with Docker & CI/CD
  ├── Optimize Resume for ATS (Google XYZ Formula)
  └── Conduct 5+ Live P2P Mock Coding & Behavioral Interviews
```

#### 💡 Daily Routine Recommendation:
- **Morning (1.5 hrs)**: 2 LeetCode Medium problems (timed: 25 mins each).
- **Afternoon (1 hr)**: CS fundamentals reading (OS/DBMS/Networks).
- **Evening (1.5 hrs)**: Hands-on project development / code commits.
"""
            return {
                "response": response,
                "suggestions": ["Blind 75 LeetCode question list", "System design interview cheatsheet", "How to write cold messages for referrals"]
            }

        # LinkedIn Networking & Referrals
        if "referral" in q or "linkedin" in q or "cold email" in q or "reach out" in q:
            response = """### 💼 How to Get Referrals on LinkedIn (High-Conversion Template)

#### 🎯 Strategy:
Don't message HR saying *"Please refer me"*. Reach out to **Senior Engineers** or **Alumni** working on the target team.

#### 📝 High-Conversion Outreach Template:
> *"Hi [Name],*
> 
> *I saw your recent engineering work at [Company Name] and was really inspired by how your team approached [Product/Engineering Feature].*
> 
> *I am a software engineer with strong experience in [Your Core Stack: e.g. Python, React, PostgreSQL], and I recently built [Project Name with GitHub link], which handles [Key Metric: e.g. 10k real-time events].*
> 
> *I noticed an open Software Engineer role (Job ID: #12345) on your team. If you have 2 minutes, would you be open to reviewing my resume for a referral? Either way, I'd love to connect and follow your work.*
> 
> *Best regards,*  
> *[Your Name] | [Portfolio/GitHub Link]"*
"""
            return {
                "response": response,
                "suggestions": ["Resume formatting tips for ATS", "Top projects for software engineer resume", "Behavioral interview questions"]
            }

        return None

    # ──────────────────────────────────────────────────────────────────────────
    # 4. DYNAMIC SYNTHESIS ENGINE
    # ──────────────────────────────────────────────────────────────────────────
    @classmethod
    def _dynamic_generate(cls, q: str, q_lower: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Dynamically synthesizes an intelligent, structured, and customized response
        for any arbitrary user query, coding doubt, or career question.
        """
        # Determine intent categories
        is_code_query = any(w in q_lower for w in ["code", "function", "program", "implement", "script", "algorithm", "syntax", "write", "how to build", "how to code", "bug", "fix", "error"])
        is_career_query = any(w in q_lower for w in ["job", "career", "interview", "resume", "cv", "salary", "fresher", "internship", "hiring", "company", "referral", "promote", "role"])
        is_system_design = any(w in q_lower for w in ["architecture", "scale", "system design", "distributed", "database", "latency", "throughput", "cache", "server", "api", "microservice"])
        is_engineering = any(w in q_lower for w in [
            "engineering", "thermodynamic", "thermodynamics", "circuit", "transistor", "signal", "control system",
            "mechanical", "electrical", "electronic", "physics", "chemistry", "fourier", "laplace", "calculus",
            "matrix", "matrices", "derivative", "integral", "newton", "bernoulli", "carnot", "maxwell", "ohm",
            "diode", "semiconductor", "microprocessor", "microcontroller", "embedded", "fluid", "fluid mechanics",
            "strain", "stress", "heat transfer", "entropy", "reynolds", "kirchhoff", "nyquist", "bode plot",
            "amplifier", "op-amp", "cad", "cam", "finite element", "aerodynamics", "kinematics", "dynamics",
            "statics", "electromagnet", "antenna", "rf", "telecom", "logic gate", "boolean algebra", "k-map"
        ])

        # Construct structured answer
        topic_header = q.strip().rstrip("?").capitalize()

        if is_code_query:
            response = f"""### 💻 Guidance on: {topic_header}

#### 🎯 Approach & Core Logic:
To implement a robust solution for **{q}**:
1. **Identify Constraints & Data Structures**: Choose the data structure that minimizes time and space complexity (e.g. Hash Map for $\\mathcal{{O}}(1)$ lookups, Two Pointers for sorted collections, or Sliding Window for subarrays).
2. **Algorithm Execution Flow**:
   - Validate input boundaries and handle empty or null inputs gracefully.
   - Execute the main transformation / processing logic with clean modular functions.
   - Maintain clear state invariants throughout loops.

#### 💡 Practical Code Example:
```python
def solution(*args, **kwargs):
    \"\"\"
    Structured implementation addressing: {q}
    \"\"\"
    # 1. Base edge case validation
    if not args:
        return None
        
    # 2. Main processing logic
    result = []
    # Implement algorithm steps cleanly
    return result

# Verification:
# print(solution(...))
```

#### ⏱️ Best Practices & Optimization:
- **Time Complexity**: Always analyze the worst-case and average-case Big-O running time.
- **Space Complexity**: Strive for in-place modifications where possible to minimize memory overhead.
- **Edge Cases**: Always test empty inputs, single element inputs, duplicates, and extreme bounds.
"""
            suggestions = [
                f"Explain time complexity for {q[:25]}",
                f"Write unit tests for this implementation",
                "How would this be tested in a FAANG interview?"
            ]
        elif is_system_design:
            response = f"""### 🏗️ Technical Architecture & Design: {topic_header}

#### 🎯 Overview & Principles:
When addressing **{q}** in enterprise software and distributed systems:
1. **High Availability & Fault Tolerance**: Ensure components have redundancy, health checks, and automatic failovers.
2. **Scalability**: Decouple stateless compute nodes (horizontal scaling) from persistence layers using caching (Redis) and read replicas.
3. **Data Consistency & Latency**: Evaluate the CAP theorem trade-offs (Consistency vs Availability under network partitions).

#### 🛠️ Recommended Architecture Flow:
- **Client Tier**: Web/Mobile clients communicating via HTTPS/WSS.
- **Gateway & Load Balancer**: Nginx / AWS ALB distributing traffic, terminating SSL, and enforcing rate limiting.
- **Service Layer**: Decoupled microservices or modular monolith built with asynchronous workers (FastAPI / Node / Spring).
- **Data & Cache Tier**: Relational primary DB (PostgreSQL) + In-memory cache (Redis) + Event Bus (Kafka/RabbitMQ).

#### 🚀 Placement & Interview Tip:
In system design interviews, start by establishing functional and non-functional requirements before sketching architecture blocks.
"""
            suggestions = [
                "Explain caching and cache invalidation strategies",
                "How to design a scalable rate limiter?",
                "Database sharding vs replication"
            ]
        elif is_engineering:
            response = f"""### ⚙️ Engineering Principles & Fundamentals: {topic_header}

#### 🎯 Core Concept & Theoretical Foundations:
When analyzing **{q}** across engineering disciplines:
1. **Governing Physical Laws & Principles**:
   - Understand the fundamental governing equations and boundary conditions dictating system behavior.
   - Examine the operational trade-offs, transfer functions, and conservation laws (energy, momentum, mass, or charge).
2. **Mathematical Formulation & Analytical Modeling**:
   - Formulate the system state equations or characteristic differential relationships.
   - Analyze stability margins, frequency responses, or thermodynamic efficiencies depending on the discipline.

#### 🛠️ Practical Engineering Applications & Industrial Practices:
- **Design & Synthesis**: Sizing components with appropriate safety margins, load factors, and tolerances.
- **Noise, Losses & Thermal Dissipation**: Mitigating non-idealities, parasitics, mechanical vibration, or thermal bottlenecks.
- **Quality & Standards**: Adhering to standard industrial specifications (e.g. IEEE, ASME, ISO, IEC).

#### 🎓 Placement & Technical Assessment Focus:
- In technical interviews and exams, examiners look for first-principles derivations, qualitative intuition behind the math, and how you evaluate real-world trade-offs under practical physical constraints.
"""
            suggestions = [
                f"Key mathematical equations for {q[:25]}",
                f"How is this evaluated in core technical interviews?",
                f"Real-world industrial applications of {q[:25]}"
            ]
        else:
            response = f"""### 🧭 Career & Technical Insights: {topic_header}

#### 🎯 Strategic Analysis:
Regarding your query on **{q}**:

1. **Foundational Understanding**:
   - Master the fundamental principles first before diving into advanced frameworks or tools.
   - Practice active learning by building practical proof-of-concept implementations and explaining concepts aloud.

2. **Actionable Implementation Steps**:
   - **Step 1**: Break the problem down into distinct, measurable daily milestones.
   - **Step 2**: Create verifiable deliverables (e.g. GitHub repositories, technical blog posts, or interactive demos).
   - **Step 3**: Benchmark your knowledge against standard tier-1 interview criteria and industry job descriptions.

3. **Key Placement Takeaways**:
   - Recruiters look for evidence of continuous problem-solving, architectural awareness, and clear communication.
   - Quantify your achievements and back up every claim with concrete project examples.
"""
            suggestions = [
                "Show coding problems related to this topic",
                "How do recruiters evaluate this skill in interviews?",
                "Create a 2-week learning roadmap for this"
            ]

        return {
            "response": response,
            "suggestions": suggestions
        }
