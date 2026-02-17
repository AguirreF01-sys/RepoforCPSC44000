"""
Title: Fermat Near Miss Finder (HW1)
File Name: main.py
External Files Required: none
External Files Created: none
Programmers: Florentino Aguirre, Deep Tadhani
Emails: florentinoaguirre@lewisu.edu, deepctadhani@lewisu.edu
Course: Software Engineering CPSC 44000-LT1
Date Submitted: 02/17/2026
Description:
    Prompts the user for n value between 3-11 (inclusive) and k greater than 10. Searches all integer pairs (x,y)
    with 10 <= x <= k and 10 <= y <= k for "near misses" to Fermat's equation
    x^n + y^n = z^n. For each (x,y), it computes S = x^n + y^n, finds integers
    z and z+1 that bracket S (z^n <= S < (z+1)^n), and computes the miss as the
    smaller of (S - z^n) or ((z+1)^n - S). The relative miss is miss / S.
    Prints a labeled report each time a new smallest relative miss is found.
Resources Used:
    - (List any websites, notes, or references you used)
"""

from typing import Tuple, Optional


def read_int(prompt: str) -> int:
    """
    Reads input from the user and returns it as an integer.

    - Displays the given prompt
    - If the user types a non-integer value, it prints an error message
      and re-prompts until a valid integer is entered.
    """
    while True:
        try:
            return int(input(prompt).strip())
        except ValueError:
            print("Invalid input. Please enter an integer.")


def read_n() -> int:
    """
    Prompts the user for the exponent n and validates it.

    - Required constraint: 2 < n < 12 (so n must be 3..11)
    - Keeps asking until a valid value is provided.
    - Returns the validated integer n.
    """
    while True:
        n = read_int("Enter n (3..11): ")
        if 3 <= n <= 11:
            return n
        print("n must be between 3 and 11 (inclusive).")


def read_k() -> int:
    """
    Prompts the user for the upper bound k and validates it.

    - Required constraint: k > 10
    - Keeps asking until a valid value is provided.
    - Returns the validated integer k.
    """
    while True:
        k = read_int("Enter k (>10): ")
        if k > 10:
            return k
        print("k must be greater than 10.")


def nth_root_floor(S: int, n: int) -> int:
    """
    Computes the integer floor of the nth root of S (i.e., floor(S^(1/n))).

    Purpose in this assignment:
    - Given S = x^n + y^n, we need to find z such that:
        z^n <= S < (z+1)^n
      This function provides that z by returning floor(S^(1/n)).

    How it works (binary search, integer-only):
    - Avoids floating point rounding errors for large integers.
    - Finds an upper bound hi where hi^n > S, then binary searches
      between lo and hi to find the largest integer lo with lo^n <= S.

    Parameters:
    - S: non-negative integer whose nth root is needed
    - n: positive integer exponent

    Returns:
    - z = floor(S^(1/n))
    """
    if S < 0:
        raise ValueError("S must be non-negative")
    if S == 0:
        return 0
    if n <= 0:
        raise ValueError("n must be positive")

    lo, hi = 0, 1

    # Expand hi until hi^n is strictly greater than S (find upper bound)
    while hi ** n <= S:
        hi *= 2

    # Binary search for the largest lo such that lo^n <= S
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if mid ** n <= S:
            lo = mid
        else:
            hi = mid

    return lo


def print_new_best(n: int, x: int, y: int, z: int, miss: int, rel: float, S: int, z_power: int, final: bool = False) -> None:
    """
    Prints a labeled report for a newly discovered best near miss.

    This is called ONLY when the program finds a smaller relative miss
    than any previous (x, y) pair tested.

    Output includes:
    - n, x, y, computed S
    - the closest z value found
    - miss (closest distance to z^n or (z+1)^n)
    - relative miss (miss / S), shown as a decimal and percent
    """
    header = "FINAL BEST NEAR MISS" if final else "NEW SMALLEST RELATIVE MISS FOUND"
    print(f"\n{header}")
    print(f"n = {n}")
    print(f"x = {x}")
    print(f"y = {y}")
    print(f"S = x^n + y^n = {S}")
    print(f"closest z = {z}")
    print(f"z^n (closest) = {z_power}")
    print(f"miss (integer) = {miss}")
    print(f"relative miss = {rel:.12g}  ({rel*100:.10g}%)")


def main() -> None:
    """
    Program entry point and main control flow.

    Steps:
    1) Read and validate inputs n and k.
    2) Loop through all integer pairs (x, y) with 10 <= x <= k and 10 <= y <= k.
    3) For each pair:
       - Compute S = x^n + y^n
       - Find z = floor(S^(1/n)) so that z^n <= S < (z+1)^n
       - Compute miss = min(S - z^n, (z+1)^n - S)
       - Choose closest_z based on which miss is smaller (z or z+1)
       - Compute relative miss = miss / S
    4) Track the smallest relative miss found so far.
       Whenever a new smallest relative miss is found, print the labeled result.
    5) After all pairs are tested, print the final best result last, then pause
       so the user can read output in the IDE console.
    """
    n = read_n()
    k = read_k()

    best_rel: float = float("inf")
    best_record: Optional[Tuple[int, int, int, int, float, int, int]] = None  # (x, y, z, miss, rel, S, z_power)

    # Loop purpose: test all x values in the required range 10..k
    for x in range(10, k + 1):
        x_pow = x ** n

        # Loop purpose: test all y values in the required range 10..k
        for y in range(10, k + 1):
            S = x_pow + (y ** n)

            # Find z such that z^n <= S < (z+1)^n
            z = nth_root_floor(S, n)

            lower = z ** n
            upper = (z + 1) ** n

            # Tricky statement: miss is the smaller distance from S to the bracketing powers
            m1 = S - lower
            m2 = upper - S

            # Determine which is smaller: m1 or m2, and set miss and closest_z accordingly
            if m1 <= m2:
                miss = m1
                closest_z = z
                closest_power = lower
            else:
                miss = m2
                closest_z = z + 1
                closest_power = upper

            rel = miss / S

            # If we found a smaller relative miss, record it and print it
            if rel < best_rel:
                best_rel = rel
                best_record = (x, y, closest_z, miss, rel, S, closest_power)
                print_new_best(n, x, y, closest_z, miss, rel, S, closest_power)

    # Ensure the smallest miss is the last thing printed
    if best_record is not None:
        x, y, z, miss, rel, S, closest_power = best_record
        # print("\nFINAL BEST (should be last output)")
        print_new_best(n, x, y, z, miss, rel, S, closest_power, final=True)

    # Pause so the user can examine the output in PyCharm
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    """
    Standard Python convention:
    - This ensures main() only runs when the file is executed directly,
      not when it is imported into another script.
    """
    main()
