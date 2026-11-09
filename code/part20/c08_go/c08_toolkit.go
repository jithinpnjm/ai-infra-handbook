// code/part20/c08_go/c08_toolkit.go
// Go equivalents of the Python toolkit in chapter 20.8.
package c08toolkit

import (
	"container/heap"
	"sort"
)

// Count is Counter: a map with a zero default for missing keys.
func Count(s string) map[rune]int {
	m := map[rune]int{}
	for _, r := range s {
		m[r]++
	}
	return m
}

// intHeap is a min-heap of ints, the shape heapq gives you for free in Python.
type intHeap []int

func (h intHeap) Len() int           { return len(h) }
func (h intHeap) Less(i, j int) bool { return h[i] < h[j] }
func (h intHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *intHeap) Push(x any)        { *h = append(*h, x.(int)) }
func (h *intHeap) Pop() any {
	old := *h
	n := len(old)
	x := old[n-1]
	*h = old[:n-1]
	return x
}

// TopK returns the k largest values, largest first, using a size-k min-heap.
func TopK(nums []int, k int) []int {
	h := &intHeap{}
	for _, v := range nums {
		heap.Push(h, v)
		if h.Len() > k {
			heap.Pop(h)
		}
	}
	out := make([]int, h.Len())
	for i := len(out) - 1; i >= 0; i-- {
		out[i] = heap.Pop(h).(int)
	}
	return out
}

// LowerBound is bisect_left: first index whose value is >= x.
func LowerBound(a []int, x int) int { return sort.SearchInts(a, x) }

// Pair is a row used to show that SliceStable keeps equal keys in input order.
type Pair struct {
	Name string
	Rank int
}

func SortByRank(p []Pair) []Pair {
	out := append([]Pair(nil), p...)
	sort.SliceStable(out, func(i, j int) bool { return out[i].Rank < out[j].Rank })
	return out
}

// MergeIntervals merges closed intervals; touching intervals merge.
func MergeIntervals(in [][2]int) [][2]int {
	a := append([][2]int(nil), in...)
	sort.Slice(a, func(i, j int) bool { return a[i][0] < a[j][0] })
	var out [][2]int
	for _, iv := range a {
		if n := len(out); n > 0 && iv[0] <= out[n-1][1] {
			if iv[1] > out[n-1][1] {
				out[n-1][1] = iv[1]
			}
		} else {
			out = append(out, iv)
		}
	}
	return out
}
