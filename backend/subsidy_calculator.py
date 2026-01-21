"""
Taiwan Government Subsidy Calculator
Based on the calculation logic from the original JavaScript implementation

This module provides functions to calculate subsidy amounts and recommend
appropriate government subsidy programs based on company information.
"""

from typing import List, Dict, Tuple


class SubsidyCalculator:
    """Calculator for Taiwan government subsidy programs"""

    # Bonus item fixed amounts (in 元)
    BONUS_VALUES = [100000, 200000, 50000, 50000, 50000]

    def __init__(
        self,
        budget: int,
        people: int,
        capital: int,
        revenue: int,
        bonus_count: int,
        project_type: str,
        marketing_types: List[str] = None,
        growth_revenue: int = 0
    ):
        """
        Initialize the subsidy calculator

        Args:
            budget: 預計所需經費 (元)
            people: 公司投保人數 (人)
            capital: 公司實收資本額 (元)
            revenue: 公司大約年度營業額 (元)
            bonus_count: 加分項目數量 (0-5)
            project_type: 類型選擇 ("研發" or "行銷")
            marketing_types: 行銷方向 (["內銷", "外銷"])
            growth_revenue: 預計行銷活動可帶來營業額成長 (元)
        """
        self.budget = budget
        self.people = people
        self.capital = capital
        self.revenue = revenue
        self.bonus_count = min(bonus_count, 5)  # Max 5 bonus items
        self.project_type = project_type
        self.marketing_types = marketing_types or []
        self.growth_revenue = growth_revenue

    def calculate_employee_grant(self) -> int:
        """
        Calculate employee-based grant
        Logic: MIN(投保人數 × 150,000, 3,000,000)

        Returns:
            Employee grant amount (元)
        """
        return min(self.people * 150000, 3000000)

    def calculate_revenue_bonus(self, grant_employee: int) -> int:
        """
        Calculate revenue bonus
        Logic:
        - Default: revenue >= 10,000,000 → +500,000
        - Special: revenue >= (grant_employee × 5) → budget × 10%

        Args:
            grant_employee: Employee grant amount

        Returns:
            Revenue bonus amount (元)
        """
        grant_revenue_bonus = 0

        # Default case: revenue >= 10M
        if self.revenue >= 10000000:
            grant_revenue_bonus = 500000

        # Special case: revenue >= (employee grant × 5)
        if self.revenue >= grant_employee * 5:
            grant_revenue_bonus = int(self.budget * 0.1)

        return grant_revenue_bonus

    def calculate_bonus_amount(self) -> int:
        """
        Calculate bonus items amount
        Logic:
        - Each item has fixed amount: [10萬, 20萬, 5萬, 5萬, 5萬]
        - 4 items: total × 0.9 (10% discount)
        - 5 items: total × 0.8 (20% discount)

        Returns:
            Total bonus amount (元)
        """
        if self.bonus_count == 0:
            return 0

        # Sum up bonus values based on count
        bonus_amount = sum(self.BONUS_VALUES[:self.bonus_count])

        # Apply discounts
        if self.bonus_count == 5:
            bonus_amount = int(bonus_amount * 0.8)
        elif self.bonus_count == 4:
            bonus_amount = int(bonus_amount * 0.9)

        return bonus_amount

    def calculate_grant_range(self) -> Tuple[int, int]:
        """
        Calculate the full grant range (min and max)

        Returns:
            Tuple of (grant_min, grant_max) in 元
        """
        # Step 1: Calculate employee grant
        grant_employee = self.calculate_employee_grant()

        # Step 2: Calculate revenue bonus
        grant_revenue_bonus = self.calculate_revenue_bonus(grant_employee)

        # Step 3: Calculate bonus amount
        bonus_amount = self.calculate_bonus_amount()

        # Step 4: Calculate grant max
        grant_max = grant_employee + grant_revenue_bonus + bonus_amount

        # Step 5: Apply upper limit
        upper_limit = min(4500000, int(self.revenue * 0.2))
        if grant_max > upper_limit:
            grant_max = upper_limit

        # Step 6: Calculate grant min (75% of max)
        grant_min = int(grant_max * 0.75)

        return grant_min, grant_max

    def get_recommended_plans(self, grant_max: int) -> List[str]:
        """
        Get recommended subsidy plans based on project type and grant amount

        Args:
            grant_max: Maximum grant amount

        Returns:
            List of recommended plan names
        """
        recommended = []
        threshold = int(grant_max * 0.8)  # 推薦基準線 = 補助最高值 × 0.8

        if self.project_type == "研發":
            # Research & Development plans
            if threshold >= 0:
                recommended.append("地方SBIR")
            if threshold >= 1500000:
                recommended.append("CITD")
            if threshold >= 2000000:
                recommended.append("中央SBIR")

        elif self.project_type == "行銷":
            # Marketing plans
            if "外銷" in self.marketing_types:
                recommended.append("開拓海外市場計畫")
            if "內銷" in self.marketing_types:
                recommended.append("內銷行銷推廣計畫（預留）")

        return recommended

    def calculate_all(self) -> Dict:
        """
        Calculate all subsidy information and return complete result

        Returns:
            Dictionary containing all calculation results
        """
        # Calculate grant range
        grant_min, grant_max = self.calculate_grant_range()

        # Get recommended plans
        recommended_plans = self.get_recommended_plans(grant_max)

        # Calculate intermediate values for transparency
        grant_employee = self.calculate_employee_grant()
        grant_revenue_bonus = self.calculate_revenue_bonus(grant_employee)
        bonus_amount = self.calculate_bonus_amount()

        return {
            "grant_min": grant_min,
            "grant_max": grant_max,
            "recommended_plans": recommended_plans,
            "breakdown": {
                "grant_employee": grant_employee,
                "grant_revenue_bonus": grant_revenue_bonus,
                "bonus_amount": bonus_amount,
                "upper_limit": min(4500000, int(self.revenue * 0.2))
            }
        }


def calculate_subsidy(
    budget: int,
    people: int,
    capital: int,
    revenue: int,
    bonus_count: int,
    project_type: str,
    marketing_types: List[str] = None,
    growth_revenue: int = 0
) -> Dict:
    """
    Convenience function to calculate subsidy without creating calculator object

    Args:
        budget: 預計所需經費 (元)
        people: 公司投保人數 (人)
        capital: 公司實收資本額 (元)
        revenue: 公司大約年度營業額 (元)
        bonus_count: 加分項目數量 (0-5)
        project_type: 類型選擇 ("研發" or "行銷")
        marketing_types: 行銷方向 (["內銷", "外銷"])
        growth_revenue: 預計行銷活動可帶來營業額成長 (元)

    Returns:
        Dictionary containing calculation results
    """
    calculator = SubsidyCalculator(
        budget=budget,
        people=people,
        capital=capital,
        revenue=revenue,
        bonus_count=bonus_count,
        project_type=project_type,
        marketing_types=marketing_types,
        growth_revenue=growth_revenue
    )
    return calculator.calculate_all()


# Example usage and testing
if __name__ == "__main__":
    print("=" * 60)
    print("Taiwan Government Subsidy Calculator - Test")
    print("=" * 60)

    # Example 1: Research project
    print("\n📊 Example 1: Research Project (研發)")
    print("-" * 60)
    result1 = calculate_subsidy(
        budget=5000000,  # 500萬預算
        people=20,  # 20人
        capital=10000000,  # 1000萬資本
        revenue=30000000,  # 3000萬營收
        bonus_count=3,  # 3個加分項目
        project_type="研發"
    )
    print(f"補助範圍: NT${result1['grant_min']:,} ~ NT${result1['grant_max']:,}")
    print(f"推薦方案: {', '.join(result1['recommended_plans'])}")
    print(f"計算明細:")
    print(f"  - 員工補助: NT${result1['breakdown']['grant_employee']:,}")
    print(f"  - 營業額加分: NT${result1['breakdown']['grant_revenue_bonus']:,}")
    print(f"  - 加分項目: NT${result1['breakdown']['bonus_amount']:,}")

    # Example 2: Marketing project
    print("\n📊 Example 2: Marketing Project (行銷)")
    print("-" * 60)
    result2 = calculate_subsidy(
        budget=3000000,  # 300萬預算
        people=15,  # 15人
        capital=5000000,  # 500萬資本
        revenue=20000000,  # 2000萬營收
        bonus_count=2,  # 2個加分項目
        project_type="行銷",
        marketing_types=["外銷", "內銷"],
        growth_revenue=5000000  # 預期成長500萬
    )
    print(f"補助範圍: NT${result2['grant_min']:,} ~ NT${result2['grant_max']:,}")
    print(f"推薦方案: {', '.join(result2['recommended_plans'])}")
    print(f"計算明細:")
    print(f"  - 員工補助: NT${result2['breakdown']['grant_employee']:,}")
    print(f"  - 營業額加分: NT${result2['breakdown']['grant_revenue_bonus']:,}")
    print(f"  - 加分項目: NT${result2['breakdown']['bonus_amount']:,}")

    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
