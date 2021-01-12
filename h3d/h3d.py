"""
Utilities for H3 distilled index conversion

based on https://github.com/uber/h3

h3d (H3 Distilled) is an original 64-bit h3 index without resolution field

Such a representation allows having a common search range for parent and it's child indexes

The following parameters have a common meaning:
- h - h3 numeric (int) representation as returned by the h3.string_to_h3()
- s - h3 hex (str) representation as returned by the h3.geo_to_h3()
- d - h3 distilled numeric (int) representation
"""

from typing import DefaultDict, List, Mapping, NewType, Optional, Tuple

import h3


#: H3 offset for resolution field
H3_RES_OFFSET = 52

#: H3 Mask for resolution
H3_RES_MASK = 0xF << H3_RES_OFFSET

#: H3 Mask for digits
H3_DIGITS_MASK = (0x1 << H3_RES_OFFSET) - 1

#: H3 bit length of one digit
H3_DIGIT_LEN = 3

#: H3 Mask for one digit
H3_DIGIT_MASK = (1 << H3_DIGIT_LEN) - 1

#: H3 Absolute maximum of resolution (inclusive)
H3_MAX_RES = 15

#: H3 index unused digit position marker
H3_UNUSED = H3_DIGIT_MASK


def h3h_to_h3d(h: int) -> int:
    """
    Returns h3 distilled from the h3 numeric index

    :param h: h3 numeric (int) representation as returned by the h3.string_to_h3()
    :returns: h3 distilled numeric (int) representation
    """
    return h & ~H3_RES_MASK


def h3s_to_h3d(s: str) -> int:
    """
    Returns h3 distilled from the h3 hex index

    :param s: h3 hex (str) representation as returned by the h3.geo_to_h3()
    :returns: h3 distilled numeric (int) representation
    """
    return h3h_to_h3d(h3.string_to_h3(s))


def h3d_resolution(d: int) -> int:
    """
    Returns resolution of the h3 distilled

    :param d: h3 distilled numeric (int) representation
    :returns: resolution
    """
    for r in range(H3_MAX_RES + 1):
        mask = H3_DIGIT_MASK << (r * H3_DIGIT_LEN)
        if (d & mask) == mask:
            continue
        break
    return H3_MAX_RES - r


def h3d_to_h3h(d: int) -> int:
    """
    Returns restored h3 numeric index from h3 distilled

    :param d: h3 distilled numeric (int) representation
    :returns: h3 numeric (int) representation as returned by the h3.string_to_h3()
    """
    return h3h_to_h3d(d) | (h3d_resolution(d) << H3_RES_OFFSET)


def h3d_to_h3s(d: int) -> int:
    """
    Returns restored h3 hex index

    :param d: h3 distilled numeric (int) representation
    :returns: h3 hex (str) representation as returned by the h3.geo_to_h3()
    """
    return h3.h3_to_string(h3d_to_h3h(d))


def h3d_unused_mask(res: int) -> int:
    """
    Returns mask for unused digits in the passed resolution

    :param res: resolution
    :returns: mask
    """
    return (1 << ((H3_MAX_RES - res) * H3_DIGIT_LEN)) - 1


def h3d_parent(d: int, res: int = None) -> int:
    """
    Returns h3 distiled of the parent

    :param d: h3 distilled numeric (int) representation
    :param res: resolution of the parent, h3d_resolution(d) - 1 by default,
        only res < h3d_resolution(d) have a meaning (wrong res doesn't lead to error anyway)
    :returns: h3 distilled of the parent
    """
    d = h3h_to_h3d(d)
    if res is None:
        res = h3d_resolution(d) - 1
    mask = h3d_unused_mask(res)
    return d | mask


def h3d_range(d: int, res: int = None) -> Tuple[int, int]:
    """
    Returns index search range for h3d subhexagones (inclusive)

    :param d: h3 distilled numeric (int) representation
    :param res: resolution to search in, h3d_resolution(d) by default,
        only res >= h3d_resolution(d) have a meaning (wrong res doesn't lead to error anyway)
    :returns: numeric range [min, max] of all subhexagone indexes (inclusive)
    """
    d = h3h_to_h3d(d)
    if res is None:
        res = h3d_resolution(d)
    mask = h3d_unused_mask(res)
    return (d & ~mask, d | mask)
