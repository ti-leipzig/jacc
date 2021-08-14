from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class ClockAttribute(ABC):
    """
    Base Class for all different Attributes that can be set in order to configure a fpga primitive
    """
    name: str
    default_value: Any
    template: str

    on = False
    value = None

    def __post_init__(self):
        self.value = self.default_value

    @abstractmethod
    def set_value(self, value):
        pass

    def instantiate_template(self):
        return self.template.replace("@value@", str(self.value))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError(f"Error, cannot compare \"{type(self)}\" and \"{type(other)}\"")

        return self.name == other.name and self.value == other.value and self.on == other.on

    def __ne__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError(f"Error, cannot compare \"{type(self)}\" and \"{type(other)}\"")

        return not (self.name == other.name and self.value == other.value and self.on == other.on)


@dataclass
class RangeAttribute(ClockAttribute):
    """
    Class for number Attributes whose value has to be within a specific range (like [0.0; 52.631])
    """
    start: Any
    end: Any
    decimal_places: int

    def set_value(self, value):
        # Check if number is of float or int and throw error if needed
        if not (isinstance(value, int) or isinstance(value, float)):
            raise TypeError(f"Error, wrong type used. Value \"{value}\" has invalid type \"{type(value)}\"")
        if value < self.start or value > self.end:
            raise ValueError(f"Error, value \"{value}\" is invalid. Value should be within [{self.start}; {self.end}]")

        self.value = value

    def instantiate_template(self):
        return self.template.replace("@value@", f"{self.value:.{self.decimal_places}f}")


@dataclass
class IncrementRangeAttribute(RangeAttribute):
    """
    Class for Range Attributes whose value can only be incremented by a specific value, e.g. 0.125.
    It also provides a generator (get_range_as_generator) which iterates through all possible values within the range.
    """
    increment: Any

    def set_and_correct_value(self, target_value: float):

        # Skip everything below if the target value is out of bounds or equal to the min/max value
        if target_value <= self.start:
            self.value = self.start
            return
        elif target_value >= self.end:
            self.value = self.end
            return

        lower_bound = self.start

        # A counter for multiplication is used here.
        # Multiplication will lead to less floating point errors than increment by adding
        counter = 0

        # Inefficient but easy to read loop
        # Could be replaced with on modulo assignment in theory
        # But should not be replaced with modulo in practice because of annoying floating point errors
        while lower_bound < target_value and lower_bound < self.end:
            lower_bound = self.increment * counter + self.start
            counter += 1

        # Chose between lower and upper bound the one that's closer to the target value
        if abs(lower_bound - target_value) < abs(lower_bound + self.increment - target_value):
            self.value = round(lower_bound, self.decimal_places)
        else:
            self.value = round(lower_bound + self.increment, self.decimal_places)

    def set_value(self, value):
        # Check if number is of float or int and throw error if needed
        if not (isinstance(value, int) or isinstance(value, float)):
            raise TypeError(f"Wrong type used. Value \"{value}\" has invalid type \"{type(value)}\"")

        self.set_and_correct_value(value)

    def get_range_as_generator(self, start=None, end=None):
        current_value = self.start if start is None or start < self.start else start
        generator_end = self.end if end is None or end > self.end else end

        while current_value <= generator_end:
            yield current_value
            current_value += self.increment


@dataclass
class OutputDivider(RangeAttribute):
    """
    Class specifically made for the output dividers (like CLKOUT1_DIVIDER).
    It seems very similar to IncrementRangeAttribute but it functionality is different.
    It does not use any of IncrementRangeAttributes' methods and does therefore not inherit from it.
    """
    increment: float
    float_divider: bool = False

    def set_value(self, value):
        # TODO
        pass

    def find_lower_and_upper_value(self, fpga_f_out_min: float, fpga_f_out_max: float):
        # TODO
        pass

@dataclass
class ListAttribute(ClockAttribute):
    """
    Class for Attributes whose values are limited to a specific list of predefined values.
    """
    values: list

    def set_value(self, value):
        if value not in self.values:
            raise ValueError(f"Error, value \"{value}\" is not valid. Valid values are {self.values}")

        self.value = value

    def instantiate_template(self):
        return self.template.replace("@value@", f"\"{self.value}\"")


@dataclass
class BoolAttribute(ClockAttribute):
    """
    Class for boolean Attributes.
    It may seem redundant, but it takes care of TypeErrors and the template instantiation
    """

    def is_valid(self) -> bool:
        return isinstance(self.value, bool)

    def set_value(self, value: bool):
        if not isinstance(self.value, bool):
            raise TypeError(f"Error, value should be of type bool. Type given was \"{type(value)}\"")

        self.value = value

    def instantiate_template(self):
        if self.value:
            return self.template.replace("@value@", "TRUE")
        else:
            return self.template.replace("@value@", "FALSE")
