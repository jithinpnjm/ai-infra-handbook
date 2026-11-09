package c08toolkit

import (
	"reflect"
	"testing"
)

func TestCountMissingKeyIsZero(t *testing.T) {
	m := Count("abracadabra")
	if m['a'] != 5 || m['z'] != 0 {
		t.Fatal(m)
	}
}

func TestTopK(t *testing.T) {
	got := TopK([]int{5, 1, 4, 9}, 2)
	if !reflect.DeepEqual(got, []int{9, 5}) {
		t.Fatal(got)
	}
	if len(TopK(nil, 3)) != 0 {
		t.Fatal("empty input")
	}
}

func TestLowerBound(t *testing.T) {
	a := []int{1, 2, 2, 2, 5}
	if LowerBound(a, 2) != 1 || LowerBound(a, 3) != 4 {
		t.Fatal("bisect_left mismatch")
	}
}

func TestSortByRankIsStable(t *testing.T) {
	got := SortByRank([]Pair{{"b", 1}, {"a", 1}, {"c", 0}})
	want := []Pair{{"c", 0}, {"b", 1}, {"a", 1}}
	if !reflect.DeepEqual(got, want) {
		t.Fatal(got)
	}
}

func TestMergeIntervals(t *testing.T) {
	got := MergeIntervals([][2]int{{3, 4}, {1, 2}, {2, 3}, {6, 7}})
	if !reflect.DeepEqual(got, [][2]int{{1, 4}, {6, 7}}) {
		t.Fatal(got)
	}
	if len(MergeIntervals(nil)) != 0 {
		t.Fatal("empty")
	}
}
