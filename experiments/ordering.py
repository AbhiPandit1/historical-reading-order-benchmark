"""Geometric reading-order algorithms applied on top of a pure line detector.

The benchmark's core question: a pure box detector loses on reading order only
because it uses a naive top-to-bottom sort. If a cheap geometric ordering stage
placed on top of the same detected boxes recovers the layout-aware order, then
reading order is a solvable add-on, not a reason to prefer a heavier segmenter.

Each function takes a list of boxes [x1,y1,x2,y2] and returns the indices in
reading order.
"""
from statistics import median


def _cx(b): return (b[0] + b[2]) / 2
def _cy(b): return (b[1] + b[3]) / 2
def _h(b): return b[3] - b[1]
def _w(b): return b[2] - b[0]


def order_topbottom(boxes):
    """Naive baseline: sort purely by vertical position."""
    return sorted(range(len(boxes)), key=lambda i: _cy(boxes[i]))


def order_columns(boxes, gap_mult=1.3):
    """Column clustering: group boxes into columns by horizontal gaps, read each
    column top-to-bottom, columns left-to-right.

    A new column starts when the x-centre jumps by more than gap_mult x the
    median line height away from the running column's x-extent — robust to lines
    of differing width and to slight skew.
    """
    if not boxes:
        return []
    n = len(boxes)
    idx = sorted(range(n), key=lambda i: _cx(boxes[i]))
    med_h = median(_h(boxes[i]) for i in range(n)) or 1.0
    # cluster centres along x with a gap threshold
    cols, cur = [], [idx[0]]
    last_cx = _cx(boxes[idx[0]])
    for i in idx[1:]:
        cx = _cx(boxes[i])
        if cx - last_cx > gap_mult * med_h * 3:  # ~3 line-heights of blank = new column
            cols.append(cur); cur = []
        cur.append(i); last_cx = cx
    cols.append(cur)
    # columns left-to-right (by min x), lines within a column top-to-bottom
    cols.sort(key=lambda c: min(boxes[i][0] for i in c))
    out = []
    for c in cols:
        out.extend(sorted(c, key=lambda i: _cy(boxes[i])))
    return out


def order_xycut(boxes, min_gap_mult=1.2):
    """Recursive XY-cut. At each step, prefer a vertical cut (separate columns,
    read left block then right); if none, take a horizontal cut (rows top-to-
    bottom); base case sorts the remaining boxes by y.
    """
    n = len(boxes)
    if n == 0:
        return []
    med_h = median(_h(b) for b in boxes) or 1.0
    med_w = median(_w(b) for b in boxes) or 1.0

    def widest_gap(intervals, thresh):
        # intervals: list of (lo, hi); find largest empty span between merged runs
        pts = sorted(intervals)
        merged = [list(pts[0])]
        for lo, hi in pts[1:]:
            if lo <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], hi)
            else:
                merged.append([lo, hi])
        best_gap, best_cut = 0, None
        for a, b in zip(merged, merged[1:]):
            g = b[0] - a[1]
            if g > best_gap:
                best_gap, best_cut = g, (a[1] + b[0]) / 2
        return best_gap, best_cut

    def rec(items):
        if len(items) <= 1:
            return items
        # vertical cut first (columns)
        xg, xcut = widest_gap([(boxes[i][0], boxes[i][2]) for i in items],
                              min_gap_mult * med_w)
        if xcut is not None and xg > min_gap_mult * med_w:
            left = [i for i in items if _cx(boxes[i]) < xcut]
            right = [i for i in items if _cx(boxes[i]) >= xcut]
            if left and right:
                return rec(left) + rec(right)
        # horizontal cut (rows)
        yg, ycut = widest_gap([(boxes[i][1], boxes[i][3]) for i in items],
                              min_gap_mult * med_h)
        if ycut is not None and yg > min_gap_mult * med_h:
            top = [i for i in items if _cy(boxes[i]) < ycut]
            bot = [i for i in items if _cy(boxes[i]) >= ycut]
            if top and bot:
                return rec(top) + rec(bot)
        # base case: no clean cut, sort by y
        return sorted(items, key=lambda i: _cy(boxes[i]))

    return rec(list(range(n)))


METHODS = {
    "topbottom": order_topbottom,
    "columns": order_columns,
    "xycut": order_xycut,
}
