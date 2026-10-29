"""Additional LeetCode-style problems plus signature metadata for the original problem bank.

Each new problem is written as a compact spec with a reference Python solution. Expected outputs
are computed from the reference solution when the module loads, so tests can't drift from the
reference, and the reference doubles as the editorial solution shown to users.
"""
import json
import textwrap
from typing import Any, Dict, List

# ─────────────────── type mapping for generated starter code ───────────────────
PY_T = {"int": "int", "double": "float", "bool": "bool", "string": "str", "int[]": "list[int]", "string[]": "list[str]",
        "int[][]": "list[list[int]]", "void": "None"}
JAVA_T = {"int": "int", "double": "double", "bool": "boolean", "string": "String", "int[]": "int[]", "string[]": "String[]",
          "int[][]": "int[][]", "void": "void"}
CPP_T = {"int": "int", "double": "double", "bool": "bool", "string": "string", "int[]": "vector<int>&", "string[]": "vector<string>&",
         "int[][]": "vector<vector<int>>&", "void": "void"}
CPP_RET = {"int": "int", "double": "double", "bool": "bool", "string": "string", "int[]": "vector<int>", "string[]": "vector<string>",
           "int[][]": "vector<vector<int>>", "void": "void"}
JS_T = {"int": "number", "double": "number", "bool": "boolean", "string": "string", "int[]": "number[]", "string[]": "string[]",
        "int[][]": "number[][]", "void": "void"}
JAVA_DEFAULT = {"int": "0", "double": "0.0", "bool": "false", "string": '""', "int[]": "new int[0]", "string[]": "new String[0]", "int[][]": "new int[0][]"}
CPP_DEFAULT = {"int": "0", "double": "0.0", "bool": "false", "string": '""', "int[]": "{}", "string[]": "{}", "int[][]": "{}"}


def _starters(fn: str, params: List[List[str]], ret: str) -> Dict[str, str]:
    py_params = ", ".join(f"{n}: {PY_T[t]}" for n, t in params)
    java_params = ", ".join(f"{JAVA_T[t]} {n}" for n, t in params)
    cpp_params = ", ".join(f"{CPP_T[t]} {n}" for n, t in params)
    js_doc = "\n".join(f" * @param {{{JS_T[t]}}} {n}" for n, t in params)
    java_body = "        // Write your code here\n" + (f"        return {JAVA_DEFAULT[ret]};\n" if ret != "void" else "")
    cpp_body = "        // Write your code here\n" + (f"        return {CPP_DEFAULT[ret]};\n" if ret != "void" else "")
    return {
        "starter_code_python": f"class Solution:\n    def {fn}(self, {py_params}) -> {PY_T[ret]}:\n        # Write your code here\n        pass\n",
        "starter_code_java": f"import java.util.*;\n\nclass Solution {{\n    public {JAVA_T[ret]} {fn}({java_params}) {{\n{java_body}    }}\n}}\n",
        "starter_code_cpp": f"#include <vector>\n#include <string>\nusing namespace std;\n\nclass Solution {{\npublic:\n    {CPP_RET[ret]} {fn}({cpp_params}) {{\n{cpp_body}    }}\n}};\n",
        "starter_code_js": f"/**\n{js_doc}\n * @return {{{JS_T[ret]}}}\n */\nvar {fn} = function({', '.join(n for n, _ in params)}) {{\n    // Write your code here\n    \n}};\n",
    }


def _ser(value: Any, typ: str) -> str:
    if typ == "string":
        return str(value)
    if typ == "bool":
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return json.dumps(value, separators=(",", ":"))
    return str(value)


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (list, tuple)):
        if value and all(isinstance(v, (list, tuple)) for v in value):
            return "; ".join(",".join(_fmt(x) for x in v) for v in value)
        return ",".join(_fmt(v) for v in value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _make(spec: Dict[str, Any], pid: int) -> Dict[str, Any]:
    ns: Dict[str, Any] = {}
    ref = textwrap.dedent(spec["ref"]).strip() + "\n"
    exec("from typing import *\nimport heapq, collections, math, bisect\n" + ref, ns)
    solver = ns["Solution"]()
    fn = getattr(solver, spec["fn"])
    tests = []
    for i, args in enumerate(spec["tests"]):
        call_args = [json.loads(json.dumps(a)) for a in args]  # deep copy
        result = fn(*call_args)
        if spec["ret"] == "void":
            result = call_args[0]
        tests.append({
            "input": "\n".join(_ser(a, t) for a, (_, t) in zip(args, spec["params"])),
            "output": _fmt(result),
            "is_hidden": i >= spec.get("public", 3),
        })
    first = tests[0]
    problem = {
        "id": pid, "title": spec["title"], "difficulty": spec["difficulty"], "category": spec["category"],
        "company_tags": spec.get("tags", ["Amazon", "Google"]),
        "problem_statement": textwrap.dedent(spec["statement"]).strip(),
        "constraints": "\n".join(f"• {c}" for c in spec["constraints"]),
        "input_format": "Each line of input is one argument, in order: " + ", ".join(f"`{n}` ({t})" for n, t in spec["params"]) + ".",
        "output_format": "Return " + {"void": "nothing (modify the array in place)"}.get(spec["ret"], f"a value of type {spec['ret']}") + ".",
        "example_input": first["input"], "example_output": first["output"],
        "explanation": spec.get("explanation", ""),
        "expected_time_complexity": spec["time"], "expected_space_complexity": spec["space"],
        "hints": spec["hints"],
        "test_cases": tests,
        "editorial": textwrap.dedent(spec["editorial"]).strip() + "\n\n```python\n" + ref + "```",
        "signature": {"fn": spec["fn"], "params": spec["params"], "returns": spec["ret"],
                      **({"unordered": True} if spec.get("unordered") else {})},
    }
    problem.update(_starters(spec["fn"], spec["params"], spec["ret"]))
    return problem


SPECS: List[Dict[str, Any]] = [
    dict(title="Contains Duplicate", difficulty="Easy", category="Arrays & Hashing", tags=["Amazon", "Apple", "Microsoft"],
         fn="containsDuplicate", params=[["nums", "int[]"]], ret="bool", time="O(N)", space="O(N)",
         statement="Given an integer array `nums`, return `true` if any value appears **at least twice** in the array, and `false` if every element is distinct.",
         constraints=["1 <= nums.length <= 10^5", "-10^9 <= nums[i] <= 10^9"],
         explanation="The value 1 appears at indices 0 and 3.",
         hints=["A brute-force pair check is O(N²). Can you remember what you've already seen?", "A hash set gives O(1) membership checks.", "Return true the moment you see a value that's already in the set."],
         editorial="Scan once, keeping a set of values seen so far. If the current value is already in the set, a duplicate exists.",
         ref="""
         class Solution:
             def containsDuplicate(self, nums):
                 seen = set()
                 for x in nums:
                     if x in seen:
                         return True
                     seen.add(x)
                 return False
         """,
         tests=[[[1, 2, 3, 1]], [[1, 2, 3, 4]], [[1, 1, 1, 3, 3, 4, 3, 2, 4, 2]], [[7]], [[-1, -2, -3, -1]]]),
    dict(title="Missing Number", difficulty="Easy", category="Arrays & Math", tags=["Amazon", "Microsoft"],
         fn="missingNumber", params=[["nums", "int[]"]], ret="int", time="O(N)", space="O(1)",
         statement="Given an array `nums` containing `n` distinct numbers in the range `[0, n]`, return the only number in the range that is **missing** from the array.",
         constraints=["n == nums.length", "1 <= n <= 10^4", "0 <= nums[i] <= n", "All numbers are unique."],
         explanation="n = 3, so the range is [0, 3]. 2 is missing.",
         hints=["What is the sum of 0..n?", "Subtract the array's sum from the expected sum.", "XOR also works: x ^ x = 0."],
         editorial="The sum of 0..n is n(n+1)/2. Subtracting the actual sum leaves the missing number. O(N) time, O(1) space.",
         ref="""
         class Solution:
             def missingNumber(self, nums):
                 n = len(nums)
                 return n * (n + 1) // 2 - sum(nums)
         """,
         tests=[[[3, 0, 1]], [[0, 1]], [[9, 6, 4, 2, 3, 5, 7, 0, 1]], [[0]], [[1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 11]]]),
    dict(title="Single Number", difficulty="Easy", category="Bit Manipulation", tags=["Amazon", "Google"],
         fn="singleNumber", params=[["nums", "int[]"]], ret="int", time="O(N)", space="O(1)",
         statement="Given a non-empty array of integers `nums`, every element appears **twice** except for one. Find that single one.\n\nYou must use only constant extra space.",
         constraints=["1 <= nums.length <= 3 * 10^4", "-3 * 10^4 <= nums[i] <= 3 * 10^4", "Each element appears twice except one."],
         hints=["What happens when you XOR a number with itself?", "a ^ a = 0 and a ^ 0 = a.", "XOR every element together."],
         editorial="XOR is commutative and a ^ a = 0, so XOR-ing all values cancels the pairs and leaves the single number.",
         ref="""
         class Solution:
             def singleNumber(self, nums):
                 result = 0
                 for x in nums:
                     result ^= x
                 return result
         """,
         tests=[[[2, 2, 1]], [[4, 1, 2, 1, 2]], [[1]], [[-3, 5, -3]], [[10, 20, 30, 20, 10]]]),
    dict(title="Move Zeroes", difficulty="Easy", category="Two Pointers", tags=["Meta", "Amazon", "Apple"],
         fn="moveZeroes", params=[["nums", "int[]"]], ret="void", time="O(N)", space="O(1)",
         statement="Given an integer array `nums`, move all `0`s to the end of it while keeping the relative order of the non-zero elements.\n\n**Note:** modify the array **in place** without making a copy.",
         constraints=["1 <= nums.length <= 10^4", "-2^31 <= nums[i] <= 2^31 - 1"],
         hints=["Keep a write pointer for the next non-zero position.", "Copy each non-zero element to the write pointer.", "Fill the remaining positions with zeros (or swap as you go)."],
         editorial="Use a write index `w`. For every non-zero value, swap it into position `w` and advance `w`. Zeros naturally move to the end.",
         ref="""
         class Solution:
             def moveZeroes(self, nums):
                 w = 0
                 for i in range(len(nums)):
                     if nums[i] != 0:
                         nums[w], nums[i] = nums[i], nums[w]
                         w += 1
         """,
         tests=[[[0, 1, 0, 3, 12]], [[0]], [[1, 2, 3]], [[0, 0, 1]], [[4, 0, 5, 0, 0, 6]]]),
    dict(title="Majority Element", difficulty="Easy", category="Arrays & Hashing", tags=["Google", "Amazon"],
         fn="majorityElement", params=[["nums", "int[]"]], ret="int", time="O(N)", space="O(1)",
         statement="Given an array `nums` of size `n`, return the majority element: the element that appears **more than ⌊n / 2⌋ times**. You may assume it always exists.",
         constraints=["1 <= n <= 5 * 10^4", "-10^9 <= nums[i] <= 10^9"],
         hints=["A hash map of counts works in O(N) space.", "Can you do it in O(1) space?", "Boyer-Moore voting: keep a candidate and a counter."],
         editorial="Boyer-Moore voting: keep a candidate and a count. When the count is 0, take the current value as the candidate; increment for matches and decrement otherwise. The majority survives.",
         ref="""
         class Solution:
             def majorityElement(self, nums):
                 candidate, count = None, 0
                 for x in nums:
                     if count == 0:
                         candidate = x
                     count += 1 if x == candidate else -1
                 return candidate
         """,
         tests=[[[3, 2, 3]], [[2, 2, 1, 1, 1, 2, 2]], [[1]], [[6, 5, 5]], [[9, 9, 9, 1, 2, 9, 3]]]),
    dict(title="Valid Palindrome", difficulty="Easy", category="Two Pointers", tags=["Meta", "Microsoft"],
         fn="isPalindrome", params=[["s", "string"]], ret="bool", time="O(N)", space="O(1)",
         statement="A phrase is a **palindrome** if, after converting all uppercase letters to lowercase and removing all non-alphanumeric characters, it reads the same forward and backward.\n\nGiven a string `s`, return `true` if it is a palindrome, or `false` otherwise.",
         constraints=["1 <= s.length <= 2 * 10^5", "s consists of printable ASCII characters."],
         explanation="\"amanaplanacanalpanama\" is a palindrome.",
         hints=["Use two pointers from both ends.", "Skip characters that aren't letters or digits.", "Compare lowercase versions."],
         editorial="Move two pointers inward, skipping non-alphanumeric characters, and compare lowercase characters. O(N) time, O(1) space.",
         ref="""
         class Solution:
             def isPalindrome(self, s):
                 i, j = 0, len(s) - 1
                 while i < j:
                     if not s[i].isalnum():
                         i += 1
                     elif not s[j].isalnum():
                         j -= 1
                     else:
                         if s[i].lower() != s[j].lower():
                             return False
                         i += 1
                         j -= 1
                 return True
         """,
         tests=[["A man a plan a canal: Panama"], ["race a car"], [" "], ["No lemon no melon"], ["0P"]]),
    dict(title="Reverse Words in a String", difficulty="Medium", category="Strings", tags=["Microsoft", "Amazon"],
         fn="reverseWords", params=[["s", "string"]], ret="string", time="O(N)", space="O(N)",
         statement="Given an input string `s`, reverse the order of the **words**. A word is a sequence of non-space characters. Return the words in reverse order joined by a single space, with no leading or trailing spaces.",
         constraints=["1 <= s.length <= 10^4", "s contains English letters, digits and spaces.", "There is at least one word in s."],
         hints=["Split on whitespace to get the words.", "Reverse the list of words.", "Join them with single spaces."],
         editorial="Split the string on whitespace (which drops extra spaces), reverse the word list, and join with single spaces.",
         ref="""
         class Solution:
             def reverseWords(self, s):
                 return " ".join(reversed(s.split()))
         """,
         tests=[["the sky is blue"], ["  hello world  "], ["a good   example"], ["single"], ["GapX makes interviews easy"]]),
    dict(title="Longest Common Prefix", difficulty="Easy", category="Strings", tags=["Google", "Adobe"],
         fn="longestCommonPrefix", params=[["strs", "string[]"]], ret="string", time="O(S)", space="O(1)",
         statement="Write a function to find the longest common prefix string amongst an array of strings. If there is no common prefix, return an empty string `\"\"`.",
         constraints=["1 <= strs.length <= 200", "0 <= strs[i].length <= 200", "strs[i] consists of lowercase English letters."],
         hints=["The prefix can't be longer than the shortest string.", "Compare characters column by column.", "Stop at the first mismatch."],
         editorial="Compare characters at each index across all strings; stop at the first index where they differ or a string ends.",
         ref="""
         class Solution:
             def longestCommonPrefix(self, strs):
                 prefix = strs[0]
                 for s in strs[1:]:
                     while not s.startswith(prefix):
                         prefix = prefix[:-1]
                 return prefix
         """,
         tests=[[["flower", "flow", "flight"]], [["interview", "internet", "interval"]], [["apple"]], [["prefix", "prefix"]], [["abc", "abd", "ab"]]]),
    dict(title="Plus One", difficulty="Easy", category="Arrays & Math", tags=["Google"],
         fn="plusOne", params=[["digits", "int[]"]], ret="int[]", time="O(N)", space="O(1)",
         statement="You are given a large integer represented as an array `digits`, where each `digits[i]` is the i-th digit (most significant first). Increment the integer by one and return the resulting array of digits.",
         constraints=["1 <= digits.length <= 100", "0 <= digits[i] <= 9", "No leading zeros except the number 0 itself."],
         hints=["Start from the last digit.", "A 9 becomes 0 and carries over.", "If every digit was 9, prepend a 1."],
         editorial="Walk from the end: if a digit is less than 9, increment it and return. Otherwise set it to 0 and continue. If all digits were 9, return [1] followed by zeros.",
         ref="""
         class Solution:
             def plusOne(self, digits):
                 for i in range(len(digits) - 1, -1, -1):
                     if digits[i] < 9:
                         digits[i] += 1
                         return digits
                     digits[i] = 0
                 return [1] + digits
         """,
         tests=[[[1, 2, 3]], [[4, 3, 2, 1]], [[9]], [[9, 9, 9]], [[1, 9, 9]]]),
    dict(title="Binary Search", difficulty="Easy", category="Binary Search", tags=["Amazon", "Microsoft"],
         fn="search", params=[["nums", "int[]"], ["target", "int"]], ret="int", time="O(log N)", space="O(1)",
         statement="Given a sorted (ascending) array of distinct integers `nums` and an integer `target`, return the index of `target` if it exists, otherwise `-1`. You must write an O(log n) algorithm.",
         constraints=["1 <= nums.length <= 10^4", "All values are distinct and sorted ascending."],
         hints=["Compare target with the middle element.", "Discard the half that can't contain the target.", "Use lo + (hi - lo) // 2 to avoid overflow."],
         editorial="Classic binary search: keep [lo, hi]; compare nums[mid] with target and shrink the range by half each step.",
         ref="""
         class Solution:
             def search(self, nums, target):
                 lo, hi = 0, len(nums) - 1
                 while lo <= hi:
                     mid = lo + (hi - lo) // 2
                     if nums[mid] == target:
                         return mid
                     if nums[mid] < target:
                         lo = mid + 1
                     else:
                         hi = mid - 1
                 return -1
         """,
         tests=[[[-1, 0, 3, 5, 9, 12], 9], [[-1, 0, 3, 5, 9, 12], 2], [[5], 5], [[1, 3, 5, 7, 9, 11, 13], 1], [[1, 3, 5, 7, 9, 11, 13], 13]]),
    dict(title="Search Insert Position", difficulty="Easy", category="Binary Search", tags=["Amazon", "Apple"],
         fn="searchInsert", params=[["nums", "int[]"], ["target", "int"]], ret="int", time="O(log N)", space="O(1)",
         statement="Given a sorted array of distinct integers and a target value, return the index if the target is found. If not, return the index where it would be inserted to keep the array sorted.",
         constraints=["1 <= nums.length <= 10^4", "nums is sorted ascending with distinct values."],
         hints=["This is binary search for the first element >= target.", "When the loop ends, lo is the insertion point."],
         editorial="Binary search for the leftmost position where nums[i] >= target; that index is the answer whether or not the target exists.",
         ref="""
         class Solution:
             def searchInsert(self, nums, target):
                 lo, hi = 0, len(nums)
                 while lo < hi:
                     mid = (lo + hi) // 2
                     if nums[mid] < target:
                         lo = mid + 1
                     else:
                         hi = mid
                 return lo
         """,
         tests=[[[1, 3, 5, 6], 5], [[1, 3, 5, 6], 2], [[1, 3, 5, 6], 7], [[1, 3, 5, 6], 0], [[2, 4, 6, 8, 10], 9]]),
    dict(title="Sqrt(x)", difficulty="Easy", category="Binary Search", tags=["Amazon", "Bloomberg"],
         fn="mySqrt", params=[["x", "int"]], ret="int", time="O(log x)", space="O(1)",
         statement="Given a non-negative integer `x`, return the square root of `x` rounded **down** to the nearest integer. You must not use any built-in exponent function or operator.",
         constraints=["0 <= x <= 2^31 - 1"],
         hints=["The answer lies between 0 and x.", "Binary search for the largest m with m * m <= x."],
         editorial="Binary search on the answer: find the largest m such that m*m <= x.",
         ref="""
         class Solution:
             def mySqrt(self, x):
                 lo, hi = 0, x
                 while lo < hi:
                     mid = (lo + hi + 1) // 2
                     if mid * mid <= x:
                         lo = mid
                     else:
                         hi = mid - 1
                 return lo
         """,
         tests=[[4], [8], [0], [1], [2147395599]]),
    dict(title="Power of Two", difficulty="Easy", category="Bit Manipulation", tags=["Google", "Amazon"],
         fn="isPowerOfTwo", params=[["n", "int"]], ret="bool", time="O(1)", space="O(1)",
         statement="Given an integer `n`, return `true` if it is a power of two. Otherwise, return `false`.",
         constraints=["-2^31 <= n <= 2^31 - 1"],
         hints=["Powers of two have exactly one set bit.", "n & (n - 1) clears the lowest set bit.", "Remember that n must be positive."],
         editorial="A positive power of two has a single 1 bit, so n > 0 and n & (n - 1) == 0.",
         ref="""
         class Solution:
             def isPowerOfTwo(self, n):
                 return n > 0 and n & (n - 1) == 0
         """,
         tests=[[1], [16], [3], [0], [-16], [1073741824]]),
    dict(title="Fibonacci Number", difficulty="Easy", category="Dynamic Programming", tags=["Amazon", "Adobe"],
         fn="fib", params=[["n", "int"]], ret="int", time="O(N)", space="O(1)",
         statement="The Fibonacci numbers are defined as F(0) = 0, F(1) = 1, and F(n) = F(n - 1) + F(n - 2) for n > 1. Given `n`, calculate F(n).",
         constraints=["0 <= n <= 30"],
         hints=["Naive recursion is exponential.", "You only need the previous two values.", "Iterate from 2 to n."],
         editorial="Iterate keeping the last two values: a, b = b, a + b. O(N) time and O(1) space.",
         ref="""
         class Solution:
             def fib(self, n):
                 a, b = 0, 1
                 for _ in range(n):
                     a, b = b, a + b
                 return a
         """,
         tests=[[2], [3], [4], [0], [30]]),
    dict(title="House Robber", difficulty="Medium", category="Dynamic Programming", tags=["Amazon", "Google", "Cisco"],
         fn="rob", params=[["nums", "int[]"]], ret="int", time="O(N)", space="O(1)",
         statement="You are a robber planning to rob houses along a street; `nums[i]` is the money in house `i`. Adjacent houses have connected alarms, so you cannot rob two adjacent houses. Return the maximum amount you can rob.",
         constraints=["1 <= nums.length <= 100", "0 <= nums[i] <= 400"],
         explanation="Rob house 1 (money = 2), house 3 (money = 9) and house 5 (money = 1): total 12.",
         hints=["For each house: rob it (plus best up to i-2) or skip it (best up to i-1).", "dp[i] = max(dp[i-1], dp[i-2] + nums[i]).", "Keep only two variables."],
         editorial="dp[i] = max(dp[i-1], dp[i-2] + nums[i]). Only the last two states are needed, giving O(1) space.",
         ref="""
         class Solution:
             def rob(self, nums):
                 prev, cur = 0, 0
                 for x in nums:
                     prev, cur = cur, max(cur, prev + x)
                 return cur
         """,
         tests=[[[1, 2, 3, 1]], [[2, 7, 9, 3, 1]], [[5]], [[2, 1, 1, 2]], [[10, 1, 1, 10, 1, 1, 10]]]),
    dict(title="Longest Increasing Subsequence", difficulty="Medium", category="Dynamic Programming", tags=["Google", "Microsoft", "Amazon"],
         fn="lengthOfLIS", params=[["nums", "int[]"]], ret="int", time="O(N log N)", space="O(N)",
         statement="Given an integer array `nums`, return the length of the longest **strictly increasing** subsequence.",
         constraints=["1 <= nums.length <= 2500", "-10^4 <= nums[i] <= 10^4"],
         explanation="The longest increasing subsequence is [2,3,7,101], so the length is 4.",
         hints=["An O(N²) DP: dp[i] = 1 + max(dp[j]) for j < i with nums[j] < nums[i].", "For O(N log N), keep the smallest tail for each length.", "Use binary search to place each number."],
         editorial="Patience sorting: maintain `tails`, where tails[k] is the smallest tail of an increasing subsequence of length k+1. Binary-search each number's position; the length of `tails` is the answer.",
         ref="""
         import bisect
         class Solution:
             def lengthOfLIS(self, nums):
                 tails = []
                 for x in nums:
                     i = bisect.bisect_left(tails, x)
                     if i == len(tails):
                         tails.append(x)
                     else:
                         tails[i] = x
                 return len(tails)
         """,
         tests=[[[10, 9, 2, 5, 3, 7, 101, 18]], [[0, 1, 0, 3, 2, 3]], [[7, 7, 7, 7]], [[1]], [[3, 10, 2, 1, 20, 4, 6, 7]]]),
    dict(title="Jump Game", difficulty="Medium", category="Greedy", tags=["Amazon", "Microsoft"],
         fn="canJump", params=[["nums", "int[]"]], ret="bool", time="O(N)", space="O(1)",
         statement="You are given an integer array `nums`. You start at the first index, and each element is your maximum jump length from that position. Return `true` if you can reach the last index, or `false` otherwise.",
         constraints=["1 <= nums.length <= 10^4", "0 <= nums[i] <= 10^5"],
         hints=["Track the furthest index reachable so far.", "If the current index is beyond that, you're stuck.", "Greedy works in one pass."],
         editorial="Greedy: keep `reach`, the furthest index reachable. If i > reach you can't continue; otherwise update reach = max(reach, i + nums[i]).",
         ref="""
         class Solution:
             def canJump(self, nums):
                 reach = 0
                 for i, x in enumerate(nums):
                     if i > reach:
                         return False
                     reach = max(reach, i + x)
                 return True
         """,
         tests=[[[2, 3, 1, 1, 4]], [[3, 2, 1, 0, 4]], [[0]], [[2, 0, 0]], [[1, 0, 1, 0]]]),
    dict(title="Unique Paths", difficulty="Medium", category="Dynamic Programming", tags=["Google", "Amazon"],
         fn="uniquePaths", params=[["m", "int"], ["n", "int"]], ret="int", time="O(M*N)", space="O(N)",
         statement="A robot is at the top-left corner of an `m x n` grid. It can only move down or right. How many unique paths are there to the bottom-right corner?",
         constraints=["1 <= m, n <= 100", "The answer fits in a 32-bit integer."],
         hints=["paths(r, c) = paths(r-1, c) + paths(r, c-1).", "The first row and column have exactly one path each.", "A single row array is enough."],
         editorial="dp[c] holds paths to the current row's column c; update dp[c] += dp[c-1] row by row. (Or use the combination C(m+n-2, m-1).)",
         ref="""
         class Solution:
             def uniquePaths(self, m, n):
                 dp = [1] * n
                 for _ in range(1, m):
                     for c in range(1, n):
                         dp[c] += dp[c - 1]
                 return dp[-1]
         """,
         tests=[[3, 7], [3, 2], [1, 1], [10, 10], [23, 12]]),
    dict(title="Edit Distance", difficulty="Hard", category="Dynamic Programming", tags=["Google", "Amazon", "Microsoft"],
         fn="minDistance", params=[["word1", "string"], ["word2", "string"]], ret="int", time="O(M*N)", space="O(N)",
         statement="Given two strings `word1` and `word2`, return the minimum number of operations (insert a character, delete a character, or replace a character) required to convert `word1` into `word2`.",
         constraints=["0 <= word1.length, word2.length <= 500", "Both strings consist of lowercase English letters."],
         explanation="horse -> rorse (replace 'h' with 'r') -> rose (remove 'r') -> ros (remove 'e').",
         hints=["dp[i][j] = edit distance between the first i chars of word1 and the first j chars of word2.", "If the characters match, dp[i][j] = dp[i-1][j-1].", "Otherwise 1 + min(insert, delete, replace)."],
         editorial="Classic Levenshtein DP. dp[i][j] = dp[i-1][j-1] if word1[i-1] == word2[j-1], else 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]).",
         ref="""
         class Solution:
             def minDistance(self, word1, word2):
                 m, n = len(word1), len(word2)
                 prev = list(range(n + 1))
                 for i in range(1, m + 1):
                     cur = [i] + [0] * n
                     for j in range(1, n + 1):
                         if word1[i - 1] == word2[j - 1]:
                             cur[j] = prev[j - 1]
                         else:
                             cur[j] = 1 + min(prev[j], cur[j - 1], prev[j - 1])
                     prev = cur
                 return prev[n]
         """,
         tests=[["horse", "ros"], ["intention", "execution"], ["abc", "abc"], ["kitten", "sitting"], ["algorithm", "altruistic"]]),
    dict(title="Longest Common Subsequence", difficulty="Medium", category="Dynamic Programming", tags=["Amazon", "Google"],
         fn="longestCommonSubsequence", params=[["text1", "string"], ["text2", "string"]], ret="int", time="O(M*N)", space="O(N)",
         statement="Given two strings `text1` and `text2`, return the length of their longest **common subsequence**, or 0 if there is none. A subsequence keeps the relative order of characters but may skip some.",
         constraints=["1 <= text1.length, text2.length <= 1000", "Lowercase English letters only."],
         explanation="The longest common subsequence is \"ace\", with length 3.",
         hints=["dp[i][j] = LCS of the prefixes of length i and j.", "Matching characters extend dp[i-1][j-1] by one.", "Otherwise take max(dp[i-1][j], dp[i][j-1])."],
         editorial="2D DP over prefixes; on a match dp[i][j] = dp[i-1][j-1] + 1, else max(dp[i-1][j], dp[i][j-1]). Rolling rows give O(N) space.",
         ref="""
         class Solution:
             def longestCommonSubsequence(self, text1, text2):
                 prev = [0] * (len(text2) + 1)
                 for a in text1:
                     cur = [0]
                     for j, b in enumerate(text2):
                         cur.append(prev[j] + 1 if a == b else max(prev[j + 1], cur[j]))
                     prev = cur
                 return prev[-1]
         """,
         tests=[["abcde", "ace"], ["abc", "abc"], ["abc", "def"], ["bsbininm", "jmjkbkjkv"], ["programming", "gaming"]]),
    dict(title="Daily Temperatures", difficulty="Medium", category="Stack", tags=["Amazon", "Meta"],
         fn="dailyTemperatures", params=[["temperatures", "int[]"]], ret="int[]", time="O(N)", space="O(N)",
         statement="Given an array of daily `temperatures`, return an array `answer` where `answer[i]` is the number of days you have to wait after day `i` to get a warmer temperature. If there is no future warmer day, `answer[i] = 0`.",
         constraints=["1 <= temperatures.length <= 10^5", "30 <= temperatures[i] <= 100"],
         hints=["Brute force checks every later day: O(N²).", "Keep a stack of indices with decreasing temperatures.", "When a warmer day arrives, pop and record the distance."],
         editorial="Monotonic decreasing stack of indices. For each day, pop all colder days from the stack and set their answer to the index difference. O(N).",
         ref="""
         class Solution:
             def dailyTemperatures(self, temperatures):
                 ans = [0] * len(temperatures)
                 stack = []
                 for i, t in enumerate(temperatures):
                     while stack and temperatures[stack[-1]] < t:
                         j = stack.pop()
                         ans[j] = i - j
                     stack.append(i)
                 return ans
         """,
         tests=[[[73, 74, 75, 71, 69, 72, 76, 73]], [[30, 40, 50, 60]], [[30, 60, 90]], [[90, 80, 70]], [[55, 38, 53, 81, 61, 93, 97, 32, 43, 78]]]),
    dict(title="Kth Largest Element in an Array", difficulty="Medium", category="Heap / Priority Queue", tags=["Meta", "Amazon", "LinkedIn"],
         fn="findKthLargest", params=[["nums", "int[]"], ["k", "int"]], ret="int", time="O(N log K)", space="O(K)",
         statement="Given an integer array `nums` and an integer `k`, return the k-th largest element in the array (in sorted order, not the k-th distinct element). Can you solve it without sorting?",
         constraints=["1 <= k <= nums.length <= 10^5", "-10^4 <= nums[i] <= 10^4"],
         hints=["Sorting is O(N log N). Can you do better?", "Keep a min-heap of size k.", "The heap's root is the k-th largest."],
         editorial="Maintain a min-heap with the k largest values seen; push each number and pop when the size exceeds k. The root is the answer. (Quickselect gives average O(N).)",
         ref="""
         import heapq
         class Solution:
             def findKthLargest(self, nums, k):
                 heap = []
                 for x in nums:
                     heapq.heappush(heap, x)
                     if len(heap) > k:
                         heapq.heappop(heap)
                 return heap[0]
         """,
         tests=[[[3, 2, 1, 5, 6, 4], 2], [[3, 2, 3, 1, 2, 4, 5, 5, 6], 4], [[1], 1], [[7, 7, 7, 7], 2], [[-1, -5, 10, 4, 3], 3]]),
    dict(title="Sort Colors", difficulty="Medium", category="Two Pointers", tags=["Microsoft", "Amazon"],
         fn="sortColors", params=[["nums", "int[]"]], ret="void", time="O(N)", space="O(1)",
         statement="Given an array `nums` with `n` objects colored red, white, or blue (0, 1 and 2), sort them **in place** so that objects of the same color are adjacent, in the order red, white, blue. Don't use the library sort.",
         constraints=["1 <= n <= 300", "nums[i] is 0, 1 or 2."],
         hints=["Counting sort works in two passes.", "Can you do it in one pass?", "Dutch national flag: low, mid and high pointers."],
         editorial="Dutch national flag: 0s are swapped to `low`, 2s to `high`, and 1s are skipped by `mid`. One pass, O(1) space.",
         ref="""
         class Solution:
             def sortColors(self, nums):
                 low, mid, high = 0, 0, len(nums) - 1
                 while mid <= high:
                     if nums[mid] == 0:
                         nums[low], nums[mid] = nums[mid], nums[low]
                         low += 1
                         mid += 1
                     elif nums[mid] == 1:
                         mid += 1
                     else:
                         nums[mid], nums[high] = nums[high], nums[mid]
                         high -= 1
         """,
         tests=[[[2, 0, 2, 1, 1, 0]], [[2, 0, 1]], [[0]], [[1, 1, 0, 0]], [[2, 2, 1, 0, 1, 2, 0]]]),
    dict(title="Minimum Size Subarray Sum", difficulty="Medium", category="Sliding Window", tags=["Meta", "Goldman Sachs"],
         fn="minSubArrayLen", params=[["target", "int"], ["nums", "int[]"]], ret="int", time="O(N)", space="O(1)",
         statement="Given an array of positive integers `nums` and a positive integer `target`, return the minimal length of a contiguous subarray whose sum is **greater than or equal to** `target`. If there is no such subarray, return 0.",
         constraints=["1 <= target <= 10^9", "1 <= nums.length <= 10^5", "1 <= nums[i] <= 10^4"],
         explanation="The subarray [4,3] has the minimal length under the constraint.",
         hints=["All numbers are positive, so a sliding window works.", "Expand the right end; shrink the left while the sum >= target.", "Track the minimum window length."],
         editorial="Sliding window: add nums[right]; while the sum >= target, record the length and remove nums[left]. Each index enters and leaves once: O(N).",
         ref="""
         class Solution:
             def minSubArrayLen(self, target, nums):
                 left, total, best = 0, 0, float('inf')
                 for right, x in enumerate(nums):
                     total += x
                     while total >= target:
                         best = min(best, right - left + 1)
                         total -= nums[left]
                         left += 1
                 return 0 if best == float('inf') else best
         """,
         tests=[[7, [2, 3, 1, 2, 4, 3]], [4, [1, 4, 4]], [11, [1, 1, 1, 1, 1, 1, 1, 1]], [15, [1, 2, 3, 4, 5]], [6, [10, 2, 3]]]),
    dict(title="Longest Repeating Character Replacement", difficulty="Medium", category="Sliding Window", tags=["Google", "Uber"],
         fn="characterReplacement", params=[["s", "string"], ["k", "int"]], ret="int", time="O(N)", space="O(1)",
         statement="You are given a string `s` of uppercase English letters and an integer `k`. You can change any character to any other uppercase letter at most `k` times. Return the length of the longest substring containing the same letter you can get after these operations.",
         constraints=["1 <= s.length <= 10^5", "0 <= k <= s.length"],
         hints=["A window is valid if (length − count of its most frequent letter) <= k.", "Expand right; shrink left when the window becomes invalid.", "Track letter counts in an array of 26."],
         editorial="Sliding window with letter counts and the max frequency seen. If window length − maxFreq > k, move left forward. The largest valid window is the answer.",
         ref="""
         class Solution:
             def characterReplacement(self, s, k):
                 count = {}
                 left = best = max_freq = 0
                 for right, ch in enumerate(s):
                     count[ch] = count.get(ch, 0) + 1
                     max_freq = max(max_freq, count[ch])
                     while right - left + 1 - max_freq > k:
                         count[s[left]] -= 1
                         left += 1
                     best = max(best, right - left + 1)
                 return best
         """,
         tests=[["ABAB", 2], ["AABABBA", 1], ["AAAA", 0], ["ABCDE", 1], ["BAAAB", 2]]),
    dict(title="Roman to Integer", difficulty="Easy", category="Strings", tags=["Amazon", "Microsoft", "Apple"],
         fn="romanToInt", params=[["s", "string"]], ret="int", time="O(N)", space="O(1)",
         statement="Roman numerals use the symbols I(1), V(5), X(10), L(50), C(100), D(500) and M(1000). A smaller value before a larger one is subtracted (IV = 4, IX = 9, XL = 40, XC = 90, CD = 400, CM = 900). Given a Roman numeral `s`, convert it to an integer.",
         constraints=["1 <= s.length <= 15", "s is a valid Roman numeral in the range [1, 3999]."],
         explanation="M = 1000, CM = 900, XC = 90 and IV = 4.",
         hints=["Map each symbol to its value.", "If a value is smaller than the next one, subtract it.", "Otherwise add it."],
         editorial="Scan left to right; subtract a symbol's value when the next symbol is larger, otherwise add it.",
         ref="""
         class Solution:
             def romanToInt(self, s):
                 val = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
                 total = 0
                 for i, ch in enumerate(s):
                     if i + 1 < len(s) and val[ch] < val[s[i + 1]]:
                         total -= val[ch]
                     else:
                         total += val[ch]
                 return total
         """,
         tests=[["III"], ["LVIII"], ["MCMXCIV"], ["XLII"], ["MMMCMXCIX"]]),
    dict(title="Is Subsequence", difficulty="Easy", category="Two Pointers", tags=["Pinterest", "Amazon"],
         fn="isSubsequence", params=[["s", "string"], ["t", "string"]], ret="bool", time="O(N)", space="O(1)",
         statement="Given two strings `s` and `t`, return `true` if `s` is a **subsequence** of `t` (formed by deleting some characters of `t` without changing the order of the rest), or `false` otherwise.",
         constraints=["1 <= s.length <= 100", "1 <= t.length <= 10^4", "Lowercase English letters only."],
         hints=["Use one pointer in each string.", "Advance the pointer in s only on a match.", "s is a subsequence if its pointer reaches the end."],
         editorial="Two pointers: walk through t, advancing the pointer in s whenever characters match. Return whether every character of s was matched.",
         ref="""
         class Solution:
             def isSubsequence(self, s, t):
                 i = 0
                 for ch in t:
                     if i < len(s) and s[i] == ch:
                         i += 1
                 return i == len(s)
         """,
         tests=[["abc", "ahbgdc"], ["axc", "ahbgdc"], ["ace", "abcde"], ["aec", "abcde"], ["gapx", "greatappsxyz"]]),
    dict(title="Partition Equal Subset Sum", difficulty="Medium", category="Dynamic Programming", tags=["Meta", "Amazon"],
         fn="canPartition", params=[["nums", "int[]"]], ret="bool", time="O(N * Sum)", space="O(Sum)",
         statement="Given an integer array `nums`, return `true` if you can partition it into two subsets with equal sums, or `false` otherwise.",
         constraints=["1 <= nums.length <= 200", "1 <= nums[i] <= 100"],
         explanation="The array can be partitioned as [1, 5, 5] and [11].",
         hints=["If the total is odd, it's impossible.", "Otherwise: is there a subset summing to total / 2?", "0/1 knapsack over possible sums."],
         editorial="Subset-sum DP: keep the set of reachable sums (or a boolean array), iterating sums downward for each number so it's used once. Check whether total/2 is reachable.",
         ref="""
         class Solution:
             def canPartition(self, nums):
                 total = sum(nums)
                 if total % 2:
                     return False
                 target = total // 2
                 reachable = {0}
                 for x in nums:
                     reachable |= {s + x for s in reachable if s + x <= target}
                 return target in reachable
         """,
         tests=[[[1, 5, 11, 5]], [[1, 2, 3, 5]], [[2, 2]], [[1, 2, 5]], [[3, 3, 3, 4, 5]]]),
    dict(title="Maximum Product Subarray", difficulty="Medium", category="Dynamic Programming", tags=["LinkedIn", "Amazon"],
         fn="maxProduct", params=[["nums", "int[]"]], ret="int", time="O(N)", space="O(1)",
         statement="Given an integer array `nums`, find a contiguous non-empty subarray that has the largest product, and return the product.",
         constraints=["1 <= nums.length <= 2 * 10^4", "-10 <= nums[i] <= 10", "The answer fits in a 32-bit integer."],
         explanation="[2,3] has the largest product, 6.",
         hints=["A negative number can turn the smallest product into the largest.", "Track both the max and min product ending at each index.", "Swap them when you meet a negative number."],
         editorial="Keep the maximum and minimum product ending at the current index; a negative number swaps their roles. The answer is the best maximum seen.",
         ref="""
         class Solution:
             def maxProduct(self, nums):
                 best = hi = lo = nums[0]
                 for x in nums[1:]:
                     if x < 0:
                         hi, lo = lo, hi
                     hi = max(x, hi * x)
                     lo = min(x, lo * x)
                     best = max(best, hi)
                 return best
         """,
         tests=[[[2, 3, -2, 4]], [[-2, 0, -1]], [[-2, 3, -4]], [[-2]], [[2, -5, -2, -4, 3]]]),
    dict(title="Longest Consecutive Sequence", difficulty="Medium", category="Arrays & Hashing", tags=["Google", "Amazon"],
         fn="longestConsecutive", params=[["nums", "int[]"]], ret="int", time="O(N)", space="O(N)",
         statement="Given an unsorted array of integers `nums`, return the length of the longest consecutive elements sequence. You must write an algorithm that runs in O(n) time.",
         constraints=["0 <= nums.length <= 10^5", "-10^9 <= nums[i] <= 10^9"],
         explanation="The longest consecutive sequence is [1, 2, 3, 4], so the length is 4.",
         hints=["Sorting is O(N log N); the target is O(N).", "Put all numbers in a set.", "Only start counting from numbers whose predecessor isn't in the set."],
         editorial="Insert everything into a set. For each number x with x−1 not in the set (a sequence start), count upward while x+1 exists. Each number is visited a constant number of times.",
         ref="""
         class Solution:
             def longestConsecutive(self, nums):
                 s = set(nums)
                 best = 0
                 for x in s:
                     if x - 1 not in s:
                         y = x
                         while y + 1 in s:
                             y += 1
                         best = max(best, y - x + 1)
                 return best
         """,
         tests=[[[100, 4, 200, 1, 3, 2]], [[0, 3, 7, 2, 5, 8, 4, 6, 0, 1]], [[1, 2, 0, 1]], [[9]], [[10, 5, 12, 3, 55, 30, 4, 11, 2]]]),
    dict(title="Subarray Sum Equals K", difficulty="Medium", category="Prefix Sums", tags=["Meta", "Google", "Amazon"],
         fn="subarraySum", params=[["nums", "int[]"], ["k", "int"]], ret="int", time="O(N)", space="O(N)",
         statement="Given an array of integers `nums` and an integer `k`, return the total number of contiguous subarrays whose sum equals `k`.",
         constraints=["1 <= nums.length <= 2 * 10^4", "-1000 <= nums[i] <= 1000", "-10^7 <= k <= 10^7"],
         hints=["A subarray sum is prefix[j] − prefix[i].", "Count how many earlier prefix sums equal prefix[j] − k.", "Store prefix-sum frequencies in a hash map (start with {0: 1})."],
         editorial="Track running prefix sums and a frequency map of prefixes seen. For each prefix p, add count[p − k] to the answer. Works with negative numbers, unlike a sliding window.",
         ref="""
         class Solution:
             def subarraySum(self, nums, k):
                 count = {0: 1}
                 prefix = ans = 0
                 for x in nums:
                     prefix += x
                     ans += count.get(prefix - k, 0)
                     count[prefix] = count.get(prefix, 0) + 1
                 return ans
         """,
         tests=[[[1, 1, 1], 2], [[1, 2, 3], 3], [[1, -1, 0], 0], [[3, 4, 7, 2, -3, 1, 4, 2], 7], [[5], 5]]),
    dict(title="Gas Station", difficulty="Medium", category="Greedy", tags=["Amazon", "Bloomberg"],
         fn="canCompleteCircuit", params=[["gas", "int[]"], ["cost", "int[]"]], ret="int", time="O(N)", space="O(1)",
         statement="There are `n` gas stations in a circle. Station `i` has `gas[i]` fuel, and it costs `cost[i]` to travel to the next station. Starting with an empty tank, return the index of the starting station from which you can travel around the circuit once clockwise, or -1 if impossible. The answer is unique if it exists.",
         constraints=["n == gas.length == cost.length", "1 <= n <= 10^5", "0 <= gas[i], cost[i] <= 10^4"],
         hints=["If total gas < total cost, it's impossible.", "If you run dry between start and i, no station in that range can be the start.", "Restart from i + 1 when the tank goes negative."],
         editorial="If sum(gas) < sum(cost) return -1. Otherwise scan once: whenever the running tank goes negative, the start must be after the current index; reset the tank.",
         ref="""
         class Solution:
             def canCompleteCircuit(self, gas, cost):
                 if sum(gas) < sum(cost):
                     return -1
                 start = tank = 0
                 for i in range(len(gas)):
                     tank += gas[i] - cost[i]
                     if tank < 0:
                         start, tank = i + 1, 0
                 return start
         """,
         tests=[[[1, 2, 3, 4, 5], [3, 4, 5, 1, 2]], [[2, 3, 4], [3, 4, 3]], [[5], [4]], [[3, 1, 1], [1, 2, 2]], [[4, 5, 2, 6, 5, 3], [3, 2, 7, 3, 2, 9]]]),
    dict(title="Rotate Array", difficulty="Medium", category="Arrays", tags=["Microsoft", "Amazon"],
         fn="rotate", params=[["nums", "int[]"], ["k", "int"]], ret="void", time="O(N)", space="O(1)",
         statement="Given an integer array `nums`, rotate the array to the right by `k` steps **in place**, where `k` is non-negative.",
         constraints=["1 <= nums.length <= 10^5", "0 <= k <= 10^5"],
         explanation="Rotate 1 step: [7,1,2,3,4,5,6]; 2 steps: [6,7,1,2,3,4,5]; 3 steps: [5,6,7,1,2,3,4].",
         hints=["k can exceed the length, so use k % n.", "Reverse the whole array.", "Then reverse the first k and the remaining n − k elements."],
         editorial="Three reversals: reverse all, reverse the first k, reverse the rest. O(N) time, O(1) space.",
         ref="""
         class Solution:
             def rotate(self, nums, k):
                 n = len(nums)
                 k %= n
                 def rev(i, j):
                     while i < j:
                         nums[i], nums[j] = nums[j], nums[i]
                         i += 1
                         j -= 1
                 rev(0, n - 1)
                 rev(0, k - 1)
                 rev(k, n - 1)
         """,
         tests=[[[1, 2, 3, 4, 5, 6, 7], 3], [[-1, -100, 3, 99], 2], [[1, 2], 5], [[1], 0], [[1, 2, 3, 4, 5, 6], 6]]),
    dict(title="Happy Number", difficulty="Easy", category="Math & Hashing", tags=["Google", "Uber"],
         fn="isHappy", params=[["n", "int"]], ret="bool", time="O(log N)", space="O(log N)",
         statement="A **happy number** is defined by repeatedly replacing the number with the sum of the squares of its digits until it equals 1 (happy), or it loops endlessly in a cycle that does not include 1 (not happy). Given `n`, return `true` if it is a happy number.",
         constraints=["1 <= n <= 2^31 - 1"],
         explanation="1² + 9² = 82 → 8² + 2² = 68 → 6² + 8² = 100 → 1² + 0² + 0² = 1.",
         hints=["Compute the next number as the sum of squared digits.", "If a number repeats, you're in a cycle.", "A set (or Floyd's cycle detection) catches it."],
         editorial="Iterate the digit-square sum, storing values in a set. Stop when you reach 1 (happy) or see a repeat (cycle).",
         ref="""
         class Solution:
             def isHappy(self, n):
                 seen = set()
                 while n != 1 and n not in seen:
                     seen.add(n)
                     n = sum(int(d) ** 2 for d in str(n))
                 return n == 1
         """,
         tests=[[19], [2], [1], [7], [116]]),
    dict(title="Count Primes", difficulty="Medium", category="Math", tags=["Amazon", "Microsoft"],
         fn="countPrimes", params=[["n", "int"]], ret="int", time="O(N log log N)", space="O(N)",
         statement="Given an integer `n`, return the number of prime numbers that are strictly less than `n`.",
         constraints=["0 <= n <= 5 * 10^6"],
         explanation="There are 4 prime numbers less than 10: 2, 3, 5, 7.",
         hints=["Testing each number individually is too slow.", "Sieve of Eratosthenes: cross out multiples of each prime.", "Start crossing out at p * p."],
         editorial="Sieve of Eratosthenes: mark multiples of each prime p starting from p*p as composite; count what remains.",
         ref="""
         class Solution:
             def countPrimes(self, n):
                 if n < 3:
                     return 0
                 is_prime = [True] * n
                 is_prime[0] = is_prime[1] = False
                 p = 2
                 while p * p < n:
                     if is_prime[p]:
                         for m in range(p * p, n, p):
                             is_prime[m] = False
                     p += 1
                 return sum(is_prime)
         """,
         tests=[[10], [0], [1], [100], [100000]]),
    dict(title="Valid Mountain Array", difficulty="Easy", category="Arrays", tags=["Google"],
         fn="validMountainArray", params=[["arr", "int[]"]], ret="bool", time="O(N)", space="O(1)",
         statement="Given an array of integers `arr`, return `true` if and only if it is a valid **mountain array**: length at least 3, strictly increasing up to some peak (not the first or last element), then strictly decreasing.",
         constraints=["1 <= arr.length <= 10^4", "0 <= arr[i] <= 10^4"],
         hints=["Walk up while values strictly increase.", "The peak can't be at either end.", "Then walk down while values strictly decrease; you must reach the end."],
         editorial="Climb while arr[i] < arr[i+1], check the peak isn't at an end, then descend while arr[i] > arr[i+1]; it's valid if you reach the last index.",
         ref="""
         class Solution:
             def validMountainArray(self, arr):
                 n, i = len(arr), 0
                 while i + 1 < n and arr[i] < arr[i + 1]:
                     i += 1
                 if i == 0 or i == n - 1:
                     return False
                 while i + 1 < n and arr[i] > arr[i + 1]:
                     i += 1
                 return i == n - 1
         """,
         tests=[[[2, 1]], [[3, 5, 5]], [[0, 3, 2, 1]], [[0, 1, 2, 3]], [[1, 3, 5, 4, 2]]]),
]


def _build_extra(start_id: int) -> List[Dict[str, Any]]:
    return [_make(spec, start_id + i) for i, spec in enumerate(SPECS)]


# ─────────────────── signatures & fixes for the original 30 problems ───────────────────
ORIGINAL_SIGNATURES: Dict[str, Dict[str, Any]] = {
    "Two Sum": {"fn": "twoSum", "params": [["nums", "int[]"], ["target", "int"]], "returns": "int[]"},
    "Valid Parentheses": {"fn": "isValid", "params": [["s", "string"]], "returns": "bool"},
    "Maximum Subarray": {"fn": "maxSubArray", "params": [["nums", "int[]"]], "returns": "int"},
    "Reverse Linked List": {"fn": "reverseList", "params": [["head", "ListNode"]], "returns": "ListNode"},
    "Best Time to Buy and Sell Stock": {"fn": "maxProfit", "params": [["prices", "int[]"]], "returns": "int"},
    "Container With Most Water": {"fn": "maxArea", "params": [["height", "int[]"]], "returns": "int"},
    "3Sum": {"fn": "threeSum", "params": [["nums", "int[]"]], "returns": "int[][]"},
    "Longest Substring Without Repeating Characters": {"fn": "lengthOfLongestSubstring", "params": [["s", "string"]], "returns": "int"},
    "Merge Two Sorted Lists": {"fn": "mergeTwoLists", "params": [["list1", "ListNode"], ["list2", "ListNode"]], "returns": "ListNode"},
    "Search in Rotated Sorted Array": {"fn": "search", "params": [["nums", "int[]"], ["target", "int"]], "returns": "int"},
    "Product of Array Except Self": {"fn": "productExceptSelf", "params": [["nums", "int[]"]], "returns": "int[]"},
    "Group Anagrams": {"fn": "groupAnagrams", "params": [["strs", "string[]"]], "returns": "string[][]"},
    "Climbing Stairs": {"fn": "climbStairs", "params": [["n", "int"]], "returns": "int"},
    "Coin Change": {"fn": "coinChange", "params": [["coins", "int[]"], ["amount", "int"]], "returns": "int"},
    "Trapping Rain Water": {"fn": "trap", "params": [["height", "int[]"]], "returns": "int"},
    "Course Schedule": {"fn": "canFinish", "params": [["numCourses", "int"], ["prerequisites", "int[][]"]], "returns": "bool"},
    "Number of Islands": {"fn": "numIslands", "params": [["grid", "char[][]"]], "returns": "int"},
    "Lowest Common Ancestor of Binary Tree": {"fn": "lowestCommonAncestor", "params": [["root", "TreeNode"], ["p", "TreeNodeRef"], ["q", "TreeNodeRef"]], "returns": "TreeNodeVal"},
    "Binary Tree Level Order Traversal": {"fn": "levelOrder", "params": [["root", "TreeNode"]], "returns": "int[][]"},
    "Invert Binary Tree": {"fn": "invertTree", "params": [["root", "TreeNode"]], "returns": "TreeNode"},
    "Word Search": {"fn": "exist", "params": [["board", "char[][]"], ["word", "string"]], "returns": "bool"},
    "Subsets": {"fn": "subsets", "params": [["nums", "int[]"]], "returns": "int[][]"},
    "Merge Intervals": {"fn": "merge", "params": [["intervals", "int[][]"]], "returns": "int[][]"},
    "Sliding Window Maximum": {"fn": "maxSlidingWindow", "params": [["nums", "int[]"], ["k", "int"]], "returns": "int[]"},
    "LRU Cache": {"design": "LRUCache"},
    "Median of Two Sorted Arrays": {"fn": "findMedianSortedArrays", "params": [["nums1", "int[]"], ["nums2", "int[]"]], "returns": "double"},
    "Valid Anagram": {"fn": "isAnagram", "params": [["s", "string"], ["t", "string"]], "returns": "bool"},
    "Top K Frequent Elements": {"fn": "topKFrequent", "params": [["nums", "int[]"], ["k", "int"]], "returns": "int[]", "unordered": True},
    "Longest Palindromic Substring": {"fn": "longestPalindrome", "params": [["s", "string"]], "returns": "string"},
    "Find Minimum in Rotated Sorted Array": {"fn": "findMin", "params": [["nums", "int[]"]], "returns": "int"},
}

# Test cases rewritten into the standard one-argument-per-line format
ORIGINAL_TEST_FIXES: Dict[str, List[Dict[str, Any]]] = {
    "Course Schedule": [
        {"input": "2\n[[1,0]]", "output": "true", "is_hidden": False},
        {"input": "2\n[[1,0],[0,1]]", "output": "false", "is_hidden": False},
        {"input": "4\n[[1,0],[2,1],[3,2]]", "output": "true", "is_hidden": True},
        {"input": "3\n[[0,1],[1,2],[2,0]]", "output": "false", "is_hidden": True},
    ],
    "Merge Intervals": [
        {"input": "[[1,3],[2,6],[8,10],[15,18]]", "output": "1,6; 8,10; 15,18", "is_hidden": False},
        {"input": "[[1,4],[4,5]]", "output": "1,5", "is_hidden": False},
        {"input": "[[1,4],[0,4]]", "output": "0,4", "is_hidden": True},
        {"input": "[[1,4],[2,3]]", "output": "1,4", "is_hidden": True},
    ],
    "LRU Cache": [
        {"input": '["LRUCache","put","put","get","put","get","put","get","get","get"]\n[[2],[1,1],[2,2],[1],[3,3],[2],[4,4],[1],[3],[4]]',
         "output": "null,null,null,1,null,-1,null,-1,3,4", "is_hidden": False},
        {"input": '["LRUCache","put","get","put","get","get"]\n[[1],[2,1],[2],[3,2],[2],[3]]', "output": "null,null,1,null,-1,2", "is_hidden": False},
        {"input": '["LRUCache","put","put","put","get","put","get","get"]\n[[2],[2,1],[1,1],[2,3],[2],[4,1],[1],[2]]',
         "output": "null,null,null,null,3,null,-1,3", "is_hidden": True},
    ],
    "Longest Palindromic Substring": [
        {"input": "babad", "output": "bab || aba", "is_hidden": False},
        {"input": "cbbd", "output": "bb", "is_hidden": False},
        {"input": "a", "output": "a", "is_hidden": True},
        {"input": "forgeeksskeegfor", "output": "geeksskeeg", "is_hidden": True},
    ],
}

ORIGINAL_EXAMPLE_FIXES: Dict[str, Dict[str, str]] = {
    "Course Schedule": {"example_input": "2\n[[1,0]]", "example_output": "true"},
    "Merge Intervals": {"example_input": "[[1,3],[2,6],[8,10],[15,18]]", "example_output": "[[1,6],[8,10],[15,18]]"},
    "LRU Cache": {"example_input": '["LRUCache","put","put","get","put","get","put","get","get","get"]\n[[2],[1,1],[2,2],[1],[3,3],[2],[4,4],[1],[3],[4]]',
                  "example_output": "[null,null,null,1,null,-1,null,-1,3,4]",
                  "input_format": "Line 1: the list of operations. Line 2: the arguments for each operation (LeetCode format).",
                  "output_format": "The result of each operation, in order (null for constructors and put)."},
}


def apply_original_fixes(problems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fixed = []
    for p in problems:
        p = dict(p)
        if p["title"] in ORIGINAL_SIGNATURES:
            p["signature"] = ORIGINAL_SIGNATURES[p["title"]]
        if p["title"] in ORIGINAL_TEST_FIXES:
            p["test_cases"] = ORIGINAL_TEST_FIXES[p["title"]]
        p.update(ORIGINAL_EXAMPLE_FIXES.get(p["title"], {}))
        fixed.append(p)
    return fixed
