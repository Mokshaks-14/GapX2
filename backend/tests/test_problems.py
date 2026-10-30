"""Every problem in the bank must be solvable: run a reference solution through the real test runner."""
import shutil
import textwrap

import pytest

from app.services.judge0 import CodeExecutionService, outputs_match
from app.services.problem_bank import ALL_PROBLEMS
from app.services.problems_extra import SPECS

ORIGINAL_SOLUTIONS = {
    "Two Sum": """
class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, x in enumerate(nums):
            if target - x in seen:
                return [seen[target - x], i]
            seen[x] = i
""",
    "Valid Parentheses": """
class Solution:
    def isValid(self, s):
        pairs, st = {')': '(', ']': '[', '}': '{'}, []
        for c in s:
            if c in pairs:
                if not st or st.pop() != pairs[c]:
                    return False
            else:
                st.append(c)
        return not st
""",
    "Maximum Subarray": """
class Solution:
    def maxSubArray(self, nums):
        best = cur = nums[0]
        for x in nums[1:]:
            cur = max(x, cur + x)
            best = max(best, cur)
        return best
""",
    "Reverse Linked List": """
class Solution:
    def reverseList(self, head):
        prev = None
        while head:
            head.next, prev, head = prev, head, head.next
        return prev
""",
    "Best Time to Buy and Sell Stock": """
class Solution:
    def maxProfit(self, prices):
        lo, best = float('inf'), 0
        for p in prices:
            lo = min(lo, p)
            best = max(best, p - lo)
        return best
""",
    "Container With Most Water": """
class Solution:
    def maxArea(self, height):
        i, j, best = 0, len(height) - 1, 0
        while i < j:
            best = max(best, (j - i) * min(height[i], height[j]))
            if height[i] < height[j]:
                i += 1
            else:
                j -= 1
        return best
""",
    "3Sum": """
class Solution:
    def threeSum(self, nums):
        nums.sort()
        res = []
        for i in range(len(nums)):
            if i and nums[i] == nums[i - 1]:
                continue
            l, r = i + 1, len(nums) - 1
            while l < r:
                s = nums[i] + nums[l] + nums[r]
                if s < 0:
                    l += 1
                elif s > 0:
                    r -= 1
                else:
                    res.append([nums[i], nums[l], nums[r]])
                    l += 1
                    while l < r and nums[l] == nums[l - 1]:
                        l += 1
        return res
""",
    "Longest Substring Without Repeating Characters": """
class Solution:
    def lengthOfLongestSubstring(self, s):
        last, left, best = {}, 0, 0
        for i, c in enumerate(s):
            if c in last and last[c] >= left:
                left = last[c] + 1
            last[c] = i
            best = max(best, i - left + 1)
        return best
""",
    "Merge Two Sorted Lists": """
class Solution:
    def mergeTwoLists(self, list1, list2):
        dummy = cur = ListNode()
        while list1 and list2:
            if list1.val <= list2.val:
                cur.next, list1 = list1, list1.next
            else:
                cur.next, list2 = list2, list2.next
            cur = cur.next
        cur.next = list1 or list2
        return dummy.next
""",
    "Search in Rotated Sorted Array": """
class Solution:
    def search(self, nums, target):
        return nums.index(target) if target in nums else -1
""",
    "Product of Array Except Self": """
class Solution:
    def productExceptSelf(self, nums):
        n = len(nums)
        out = [1] * n
        p = 1
        for i in range(n):
            out[i] = p
            p *= nums[i]
        p = 1
        for i in range(n - 1, -1, -1):
            out[i] *= p
            p *= nums[i]
        return out
""",
    "Group Anagrams": """
class Solution:
    def groupAnagrams(self, strs):
        groups = {}
        for s in strs:
            groups.setdefault(''.join(sorted(s)), []).append(s)
        return list(groups.values())
""",
    "Climbing Stairs": """
class Solution:
    def climbStairs(self, n):
        a, b = 1, 1
        for _ in range(n):
            a, b = b, a + b
        return a
""",
    "Coin Change": """
class Solution:
    def coinChange(self, coins, amount):
        dp = [0] + [float('inf')] * amount
        for a in range(1, amount + 1):
            for c in coins:
                if c <= a:
                    dp[a] = min(dp[a], dp[a - c] + 1)
        return -1 if dp[amount] == float('inf') else dp[amount]
""",
    "Trapping Rain Water": """
class Solution:
    def trap(self, height):
        l, r, lm, rm, w = 0, len(height) - 1, 0, 0, 0
        while l < r:
            if height[l] < height[r]:
                lm = max(lm, height[l])
                w += lm - height[l]
                l += 1
            else:
                rm = max(rm, height[r])
                w += rm - height[r]
                r -= 1
        return w
""",
    "Course Schedule": """
class Solution:
    def canFinish(self, numCourses, prerequisites):
        indeg = [0] * numCourses
        adj = [[] for _ in range(numCourses)]
        for a, b in prerequisites:
            adj[b].append(a)
            indeg[a] += 1
        q = [i for i in range(numCourses) if indeg[i] == 0]
        seen = 0
        while q:
            n = q.pop()
            seen += 1
            for m in adj[n]:
                indeg[m] -= 1
                if indeg[m] == 0:
                    q.append(m)
        return seen == numCourses
""",
    "Number of Islands": """
class Solution:
    def numIslands(self, grid):
        R, C, count = len(grid), len(grid[0]), 0
        def sink(r, c):
            if 0 <= r < R and 0 <= c < C and grid[r][c] == '1':
                grid[r][c] = '0'
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    sink(r + dr, c + dc)
        for r in range(R):
            for c in range(C):
                if grid[r][c] == '1':
                    count += 1
                    sink(r, c)
        return count
""",
    "Lowest Common Ancestor of Binary Tree": """
class Solution:
    def lowestCommonAncestor(self, root, p, q):
        if not root or root is p or root is q:
            return root
        l = self.lowestCommonAncestor(root.left, p, q)
        r = self.lowestCommonAncestor(root.right, p, q)
        return root if l and r else l or r
""",
    "Binary Tree Level Order Traversal": """
class Solution:
    def levelOrder(self, root):
        res, level = [], [root] if root else []
        while level:
            res.append([n.val for n in level])
            level = [c for n in level for c in (n.left, n.right) if c]
        return res
""",
    "Invert Binary Tree": """
class Solution:
    def invertTree(self, root):
        if root:
            root.left, root.right = self.invertTree(root.right), self.invertTree(root.left)
        return root
""",
    "Word Search": """
class Solution:
    def exist(self, board, word):
        R, C = len(board), len(board[0])
        def dfs(r, c, i):
            if i == len(word):
                return True
            if not (0 <= r < R and 0 <= c < C) or board[r][c] != word[i]:
                return False
            tmp, board[r][c] = board[r][c], '#'
            ok = any(dfs(r + dr, c + dc, i + 1) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            board[r][c] = tmp
            return ok
        return any(dfs(r, c, 0) for r in range(R) for c in range(C))
""",
    "Subsets": """
class Solution:
    def subsets(self, nums):
        res = [[]]
        for x in nums:
            res += [s + [x] for s in res]
        return res
""",
    "Merge Intervals": """
class Solution:
    def merge(self, intervals):
        out = []
        for s, e in sorted(intervals):
            if out and s <= out[-1][1]:
                out[-1][1] = max(out[-1][1], e)
            else:
                out.append([s, e])
        return out
""",
    "Sliding Window Maximum": """
from collections import deque
class Solution:
    def maxSlidingWindow(self, nums, k):
        dq, out = deque(), []
        for i, x in enumerate(nums):
            while dq and nums[dq[-1]] <= x:
                dq.pop()
            dq.append(i)
            if dq[0] <= i - k:
                dq.popleft()
            if i >= k - 1:
                out.append(nums[dq[0]])
        return out
""",
    "LRU Cache": """
from collections import OrderedDict
class LRUCache:
    def __init__(self, capacity):
        self.cap, self.d = capacity, OrderedDict()
    def get(self, key):
        if key not in self.d:
            return -1
        self.d.move_to_end(key)
        return self.d[key]
    def put(self, key, value):
        self.d[key] = value
        self.d.move_to_end(key)
        if len(self.d) > self.cap:
            self.d.popitem(last=False)
""",
    "Median of Two Sorted Arrays": """
class Solution:
    def findMedianSortedArrays(self, nums1, nums2):
        a = sorted(nums1 + nums2)
        n = len(a)
        return float(a[n // 2]) if n % 2 else (a[n // 2 - 1] + a[n // 2]) / 2
""",
    "Valid Anagram": """
class Solution:
    def isAnagram(self, s, t):
        return sorted(s) == sorted(t)
""",
    "Top K Frequent Elements": """
from collections import Counter
class Solution:
    def topKFrequent(self, nums, k):
        return [x for x, _ in Counter(nums).most_common(k)]
""",
    "Longest Palindromic Substring": """
class Solution:
    def longestPalindrome(self, s):
        best = ''
        for i in range(len(s)):
            for l, r in ((i, i), (i, i + 1)):
                while l >= 0 and r < len(s) and s[l] == s[r]:
                    l -= 1
                    r += 1
                if r - l - 1 > len(best):
                    best = s[l + 1:r]
        return best
""",
    "Find Minimum in Rotated Sorted Array": """
class Solution:
    def findMin(self, nums):
        lo, hi = 0, len(nums) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] > nums[hi]:
                lo = mid + 1
            else:
                hi = mid
        return nums[lo]
""",
}

EXTRA_SOLUTIONS = {spec["title"]: textwrap.dedent(spec["ref"]) for spec in SPECS}
BY_TITLE = {p["title"]: p for p in ALL_PROBLEMS}


def test_bank_size_and_unique_titles():
    titles = [p["title"] for p in ALL_PROBLEMS]
    assert len(titles) == len(set(titles))
    assert len(ALL_PROBLEMS) >= 60
    assert all(p.get("signature") for p in ALL_PROBLEMS)


@pytest.mark.parametrize("title", list(BY_TITLE))
def test_reference_solution_passes(title):
    code = ORIGINAL_SOLUTIONS.get(title) or EXTRA_SOLUTIONS.get(title)
    assert code, f"no reference solution for {title}"
    p = BY_TITLE[title]
    res = CodeExecutionService.execute_code(code, "python", p["test_cases"], p["signature"])
    assert res["status"] == "Accepted", (title, res["message"], res.get("error_details"), res["test_results"])


def test_wrong_answer_is_detected():
    p = BY_TITLE["Two Sum"]
    bad = "class Solution:\n    def twoSum(self, nums, target):\n        return [0, 0]\n"
    res = CodeExecutionService.execute_code(bad, "python", p["test_cases"], p["signature"])
    assert res["status"] == "Wrong Answer"


def test_hidden_cases_are_masked():
    p = BY_TITLE["Contains Duplicate"]
    res = CodeExecutionService.execute_code(EXTRA_SOLUTIONS["Contains Duplicate"], "python", p["test_cases"], p["signature"])
    hidden = [r for r in res["test_results"] if r["is_hidden"]]
    assert hidden and all(r["input"] == "(hidden test case)" for r in hidden)


def test_user_print_does_not_break_output():
    p = BY_TITLE["Fibonacci Number"]
    code = "class Solution:\n    def fib(self, n):\n        print('debug', n)\n        a, b = 0, 1\n        for _ in range(n):\n            a, b = b, a + b\n        return a\n"
    res = CodeExecutionService.execute_code(code, "python", p["test_cases"], p["signature"])
    assert res["status"] == "Accepted"
    assert "debug" in res["test_results"][0]["stdout"]


def test_infinite_loop_times_out():
    p = BY_TITLE["Fibonacci Number"]
    code = "class Solution:\n    def fib(self, n):\n        while True:\n            n += 1\n"
    res = CodeExecutionService.execute_code(code, "python", p["test_cases"][:1], p["signature"])
    assert res["status"] == "Time Limit Exceeded"


def test_syntax_error_reports_line():
    res = CodeExecutionService.execute_code("class Solution:\n    def fib(self, n)\n        return n\n", "python", BY_TITLE["Fibonacci Number"]["test_cases"])
    assert res["status"] == "Compile Error"
    assert res["error_details"]["line_number"] == 2


def test_output_matching_rules():
    assert outputs_match("2.0", "2")
    assert outputs_match("aba", "bab || aba")
    assert outputs_match("tan,nat; bat; eat,tea,ate", "eat,tea,ate; tan,nat; bat")
    assert outputs_match("2,1", "1,2", unordered=True)
    assert not outputs_match("2,1", "1,2")


JS_SOLUTIONS = {
    "Two Sum": "var twoSum = function(nums, target) {\n  const m = new Map();\n  for (let i = 0; i < nums.length; i++) { if (m.has(target - nums[i])) return [m.get(target - nums[i]), i]; m.set(nums[i], i); }\n};",
    "Reverse Linked List": "var reverseList = function(head) { let prev = null; while (head) { const n = head.next; head.next = prev; prev = head; head = n; } return prev; };",
    "Move Zeroes": "var moveZeroes = function(nums) { let w = 0; for (let i = 0; i < nums.length; i++) if (nums[i] !== 0) { [nums[w], nums[i]] = [nums[i], nums[w]]; w++; } };",
    "Number of Islands": "var numIslands = function(grid) { let c = 0; const R = grid.length, C = grid[0].length; const s = (r, k) => { if (r < 0 || k < 0 || r >= R || k >= C || grid[r][k] !== '1') return; grid[r][k] = '0'; s(r+1,k); s(r-1,k); s(r,k+1); s(r,k-1); }; for (let r = 0; r < R; r++) for (let k = 0; k < C; k++) if (grid[r][k] === '1') { c++; s(r, k); } return c; };",
    "LRU Cache": "class LRUCache { constructor(c) { this.c = c; this.m = new Map(); } get(k) { if (!this.m.has(k)) return -1; const v = this.m.get(k); this.m.delete(k); this.m.set(k, v); return v; } put(k, v) { this.m.delete(k); this.m.set(k, v); if (this.m.size > this.c) this.m.delete(this.m.keys().next().value); } }",
}


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
@pytest.mark.parametrize("title", list(JS_SOLUTIONS))
def test_javascript_runner(title):
    p = BY_TITLE[title]
    res = CodeExecutionService.execute_code(JS_SOLUTIONS[title], "javascript", p["test_cases"], p["signature"])
    assert res["status"] == "Accepted", (title, res)


JAVA_SOLUTIONS = {
    "Two Sum": "import java.util.*;\nclass Solution {\n    public int[] twoSum(int[] nums, int target) {\n        Map<Integer,Integer> m = new HashMap<>();\n        for (int i = 0; i < nums.length; i++) { if (m.containsKey(target - nums[i])) return new int[]{m.get(target - nums[i]), i}; m.put(nums[i], i); }\n        return new int[0];\n    }\n}",
    "Merge Intervals": "import java.util.*;\nclass Solution {\n    public int[][] merge(int[][] in) {\n        Arrays.sort(in, (a, b) -> a[0] - b[0]); List<int[]> out = new ArrayList<>();\n        for (int[] x : in) { if (!out.isEmpty() && x[0] <= out.get(out.size()-1)[1]) out.get(out.size()-1)[1] = Math.max(out.get(out.size()-1)[1], x[1]); else out.add(x); }\n        return out.toArray(new int[0][]);\n    }\n}",
    "Binary Tree Level Order Traversal": "import java.util.*;\nclass Solution {\n    public List<List<Integer>> levelOrder(TreeNode root) {\n        List<List<Integer>> res = new ArrayList<>(); if (root == null) return res; Deque<TreeNode> q = new ArrayDeque<>(); q.add(root);\n        while (!q.isEmpty()) { List<Integer> lvl = new ArrayList<>(); for (int n = q.size(); n > 0; n--) { TreeNode t = q.poll(); lvl.add(t.val); if (t.left != null) q.add(t.left); if (t.right != null) q.add(t.right); } res.add(lvl); }\n        return res;\n    }\n}",
    "Group Anagrams": "import java.util.*;\nclass Solution {\n    public List<List<String>> groupAnagrams(String[] strs) {\n        Map<String, List<String>> m = new LinkedHashMap<>();\n        for (String s : strs) { char[] c = s.toCharArray(); Arrays.sort(c); m.computeIfAbsent(new String(c), k -> new ArrayList<>()).add(s); }\n        return new ArrayList<>(m.values());\n    }\n}",
    "Sort Colors": "class Solution {\n    public void sortColors(int[] nums) { int[] c = new int[3]; for (int x : nums) c[x]++; int i = 0; for (int v = 0; v < 3; v++) while (c[v]-- > 0) nums[i++] = v; }\n}",
    "Number of Islands": "class Solution {\n    public int numIslands(char[][] g) { int c = 0; for (int r = 0; r < g.length; r++) for (int k = 0; k < g[0].length; k++) if (g[r][k] == '1') { c++; sink(g, r, k); } return c; }\n    void sink(char[][] g, int r, int k) { if (r < 0 || k < 0 || r >= g.length || k >= g[0].length || g[r][k] != '1') return; g[r][k] = '0'; sink(g, r+1, k); sink(g, r-1, k); sink(g, r, k+1); sink(g, r, k-1); }\n}",
    "LRU Cache": "import java.util.*;\nclass LRUCache {\n    private final int cap; private final LinkedHashMap<Integer,Integer> m = new LinkedHashMap<>(16, 0.75f, true);\n    public LRUCache(int capacity) { cap = capacity; }\n    public int get(int key) { return m.getOrDefault(key, -1); }\n    public void put(int key, int value) { m.put(key, value); if (m.size() > cap) m.remove(m.keySet().iterator().next()); }\n}",
}


@pytest.mark.skipif(shutil.which("javac") is None, reason="JDK not installed")
@pytest.mark.parametrize("title", list(JAVA_SOLUTIONS))
def test_java_runner(title):
    p = BY_TITLE[title]
    res = CodeExecutionService.execute_code(JAVA_SOLUTIONS[title], "java", p["test_cases"], p["signature"])
    assert res["status"] == "Accepted", (title, res["message"], res.get("error_details"), res["test_results"][:2])


def test_cpp_runs_or_reports_missing_compiler():
    p = BY_TITLE["Fibonacci Number"]
    code = "class Solution {\npublic:\n    int fib(int n) { int a = 0, b = 1; for (int i = 0; i < n; i++) { int t = a + b; a = b; b = t; } return a; }\n};"
    res = CodeExecutionService.execute_code(code, "cpp", p["test_cases"], p["signature"])
    if shutil.which("g++"):
        assert res["status"] == "Accepted", res
    else:
        assert res["status"] == "Runtime Not Installed"


C_SOLUTIONS = {
    "Two Sum": "int* twoSum(int* nums, int numsSize, int target, int* returnSize) {\n    int* r = malloc(2 * sizeof(int)); *returnSize = 2;\n    for (int i = 0; i < numsSize; i++) for (int j = i + 1; j < numsSize; j++) if (nums[i] + nums[j] == target) { r[0] = i; r[1] = j; return r; }\n    *returnSize = 0; return r;\n}",
    "Reverse Linked List": "struct ListNode* reverseList(struct ListNode* head) {\n    struct ListNode* prev = NULL;\n    while (head) { struct ListNode* n = head->next; head->next = prev; prev = head; head = n; }\n    return prev;\n}",
    "Valid Palindrome": "bool isPalindrome(char* s) {\n    int i = 0, j = (int)strlen(s) - 1;\n    while (i < j) { if (!isalnum((unsigned char)s[i])) i++; else if (!isalnum((unsigned char)s[j])) j--; else { if (tolower((unsigned char)s[i]) != tolower((unsigned char)s[j])) return false; i++; j--; } }\n    return true;\n}",
    "Move Zeroes": "void moveZeroes(int* nums, int numsSize) {\n    int w = 0; for (int i = 0; i < numsSize; i++) if (nums[i]) { int t = nums[w]; nums[w] = nums[i]; nums[i] = t; w++; }\n}",
    "Longest Common Prefix": "char* longestCommonPrefix(char** strs, int strsSize) {\n    int n = strlen(strs[0]);\n    for (int i = 1; i < strsSize; i++) { int k = 0; while (k < n && strs[i][k] && strs[i][k] == strs[0][k]) k++; n = k; }\n    char* r = malloc(n + 1); memcpy(r, strs[0], n); r[n] = 0; return r;\n}",
    "Lowest Common Ancestor of Binary Tree": "struct TreeNode* lowestCommonAncestor(struct TreeNode* root, struct TreeNode* p, struct TreeNode* q) {\n    if (!root || root == p || root == q) return root;\n    struct TreeNode* l = lowestCommonAncestor(root->left, p, q); struct TreeNode* r = lowestCommonAncestor(root->right, p, q);\n    return (l && r) ? root : (l ? l : r);\n}",
    "Median of Two Sorted Arrays": "double findMedianSortedArrays(int* a, int n, int* b, int m) {\n    int* c = malloc(sizeof(int) * (n + m)); int i = 0, j = 0, k = 0;\n    while (i < n || j < m) c[k++] = (j >= m || (i < n && a[i] <= b[j])) ? a[i++] : b[j++];\n    return (n + m) % 2 ? c[(n + m) / 2] : (c[(n + m) / 2 - 1] + c[(n + m) / 2]) / 2.0;\n}",
}


def test_c_starter_is_detected_as_unimplemented():
    p = BY_TITLE["Two Sum"]
    res = CodeExecutionService.execute_code(p["starter_code_c"], "c", p["test_cases"], p["signature"])
    assert res["status"] == "Wrong Answer" and "starter" in res["message"]


def test_c_unsupported_problem_explains_itself():
    p = BY_TITLE["Merge Intervals"]
    res = CodeExecutionService.execute_code("int x(void){return 1;}\nint y(void){return 2;}", "c", p["test_cases"], p["signature"])
    assert res["status"] == "Unsupported Signature"


@pytest.mark.skipif(shutil.which("gcc") is None, reason="gcc not installed")
@pytest.mark.parametrize("title", list(C_SOLUTIONS))
def test_c_runner(title):
    p = BY_TITLE[title]
    res = CodeExecutionService.execute_code(C_SOLUTIONS[title], "c", p["test_cases"], p["signature"])
    assert res["status"] == "Accepted", (title, res["message"], res.get("error_details"), res["test_results"][:2])
