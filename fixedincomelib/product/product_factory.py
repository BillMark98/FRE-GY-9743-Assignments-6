"""Convention-driven factory adapted from the instructor template.

Swap axis1 is tenor or start-offset x tenor. FRA uses start-offset x end-offset,
with both offsets measured from value_date, or two explicit ISO dates.
"""

from typing import Any
from fixedincomelib.date import Date, TermOrDate, add_period
from fixedincomelib.market.data_conventions import (
    CompoundingMethod, DataConvention, DataConventionFRA,
    DataConventionRFRSwap, DataConventionOvernightIndexBasisSwap,
)
from fixedincomelib.product.product_interfaces import ProductBuilderRegistry
from fixedincomelib.product.linear_products import ProductFRA, ProductRFRSwap, ProductOvernightIndexBasisSwap
from fixedincomelib.product.utilities import PayOrReceive


class ProductFactory:
    @classmethod
    def create_product_from_data_convention(
        cls,
        value_date: Date,
        axis1: str,
        data_convention: DataConvention,
        values: float,
        **kwargs: Any,
    ):

        convention_obj: DataConvention = data_convention
        prod_type = convention_obj.type()
        func = ProductBuilderRegistry().get(prod_type)
        return func(value_date, axis1, convention_obj, values, **kwargs)

    @classmethod
    def create_rfr_swap(
        cls,
        value_date: Date,
        axis1: str,
        data_convention: DataConventionRFRSwap,
        values: float,
        **kwargs: Any,
    ) -> ProductRFRSwap:
        """HW6 task 3: fixed vs compounded overnight swap from a convention.

        ``values`` is the quote: the swap's fixed rate (decimal).
        kwargs: notional (default 1e4, as create_fra), pay_or_rec ('receive' =
        receive fixed / pay floating), spread on the floating leg (default 0).
        """
        bdc = data_convention.business_day_convention
        holidays = data_convention.holiday_convention
        effective_date, term_or_termination = cls._resolve_swap_dates(value_date, axis1, bdc, holidays)
        # Every contractual field is read from the convention's typed accessors,
        # which wrap the convention's own string tokens ("SOFR-1B", "1Y", "2D",
        # "F", "USGS", ...).  The product therefore serializes to exactly the same
        # dict as one built by hand from those tokens -- the notebook checks this
        # (direct.serialize() == created.serialize()).
        accrual_period = data_convention.acc_period
        return ProductRFRSwap(
            effective_date,
            term_or_termination,
            data_convention.payment_offset,
            data_convention.index_str,
            values,                                            # quote = fixed rate
            PayOrReceive.from_string(kwargs.get("pay_or_rec", "receive")),
            kwargs.get("notional", 1e4),
            accrual_period,
            data_convention.acc_basis,
            accrual_period,                                    # one ACCRUAL_PERIOD in the convention -> both legs
            bdc,
            holidays,
            kwargs.get("spread", 0.0),
            data_convention.compounding_method,
        )

    @classmethod
    def create_overnight_index_basis_swap(
        cls,
        value_date: Date,
        axis1: str,
        data_convention: DataConventionOvernightIndexBasisSwap,
        values: float,
        **kwargs: Any,
    ) -> ProductOvernightIndexBasisSwap:
        """HW6 task 4: overnight index basis swap from a convention.

        ``values`` is the quote: the spread added to leg 1 (decimal).  Leg 1 is the
        convention's BASIS_OI_INDEX and leg 2 its REFERENCE_OI_INDEX.
        kwargs: notional (default 1e4); direction as pay_or_rec_leg_1, or the
        generic pay_or_rec the dispatcher passes for every product
        ('receive' = receive leg 1 / pay leg 2).
        """
        bdc = data_convention.business_day_convention
        holidays = data_convention.holiday_convention
        effective_date, term_or_termination = cls._resolve_swap_dates(value_date, axis1, bdc, holidays)
        direction = kwargs.get("pay_or_rec_leg_1", kwargs.get("pay_or_rec", "receive"))
        return ProductOvernightIndexBasisSwap(
            effective_date,
            term_or_termination,
            data_convention.payment_offset,
            data_convention.index_1_str,
            data_convention.index_2_str,
            values,                                            # quote = spread over leg 1
            PayOrReceive.from_string(direction),
            kwargs.get("notional", 1e4),
            data_convention.acc_period_1,
            data_convention.acc_basis,
            data_convention.acc_period_2,
            bdc,
            holidays,
            data_convention.compounding_method,
        )

    @classmethod
    def _resolve_swap_dates(cls, value_date, axis1, bdc, holidays):
        """Map a swap axis1 to (effective date, TermOrDate end), both swap types.

        Swap rule (unlike the FRA, whose two offsets are both measured from
        value_date):
          * "1Y"                     spot start: effective = value_date, end = 1Y from it
          * "3Mx1Y"                  forward start: effective = value_date + 3M
                                     (rolled bdc/holidays), then RUN for 1Y
          * "2026-04-02x2027-04-02"  explicit start and end dates
          * "2026-04-02x1Y"          explicit start, then run for 1Y
        The end is passed on as a TermOrDate, unresolved.  The swap constructor
        rolls a tenor on its index calendar, and serializes the tenor as written,
        so "1Y" stays "1Y" (not a date).  "Spot" here is the value date itself:
        the conventions carry no settlement lag, and the product constructor rolls
        a non-business effective date forward.
        """
        start, end = cls._tokenize_axis1(axis1)
        if end is None:
            return value_date, start
        if start.is_term():
            effective_date = add_period(value_date, start.get_term(), bdc, holidays)
        else:
            effective_date = start.get_date()
        return effective_date, end

    @classmethod
    def create_fra(cls, value_date, axis1, data_convention, values, **kwargs):
        start, end = cls._tokenize_axis1(axis1)
        bdc = data_convention.business_day_convention
        holidays = data_convention.holiday_convention
        if start.is_term():
            effective_date = add_period(value_date, start.get_term(), bdc, holidays)
            termination_date = add_period(value_date, end.get_term(), bdc, holidays)
        else:
            effective_date = start.get_date()
            termination_date = end.get_date()
        return ProductFRA(
            effective_date, TermOrDate(termination_date), data_convention.index_str,
            values, PayOrReceive.from_string(kwargs.get("pay_or_rec", "receive")),
            kwargs.get("notional", 1e4), data_convention.acc_basis, bdc, holidays,
        )

    @staticmethod
    def _tokenize_axis1(axis1):
        tokens = axis1.strip().replace("X", "x").split("x")
        first = TermOrDate(tokens[0].strip())
        second = TermOrDate(tokens[1].strip()) if len(tokens) == 2 else None
        return first, second


ProductBuilderRegistry().register(DataConventionFRA.type(), ProductFactory.create_fra)
ProductBuilderRegistry().register(DataConventionRFRSwap.type(), ProductFactory.create_rfr_swap)
ProductBuilderRegistry().register(DataConventionOvernightIndexBasisSwap.type(),
                                  ProductFactory.create_overnight_index_basis_swap)
