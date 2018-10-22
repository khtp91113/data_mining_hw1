from itertools import combinations
import sys
import time
support = {}

def loadDataSet(file_path):
    # read file
    dataSet = open(file_path, 'r')
    data = []
    tmp = []
    now = 1
    # deal with IBM dataset, split with whitespace, combine products with same transaction id
    while True:
        string = dataSet.readline()
        if string == '':
            data.append(tmp)
            break
        customer, transaction, product = string.split()
        if now == transaction:
            tmp.append(product)
        else:
            data.append(tmp)
            tmp = [product]
            now = transaction
    return data

def generate_L1(data, min_support):
    count = {}
    # count every item appear times
    for transaction in data:
        for item in transaction:
            if item in count:
                count[item] += 1
            else:
                count[item] = 1
    total = len(data)
    L1 = []
    # calculate support, return L1 which support value is larger than min_support
    for item in count:
        if float(count[item])/total >= min_support:
            L1.append(item)
    L1.sort()
    return L1, count

# define tree Node
class treeNode:
    def __init__(self, index):
        # node id
        self.index = index
        # support value
        self.value = 0
        # child node
        self.child = []
        # parent node
        self.parent = None
        # item name
        self.name = ''

# compare function for sorting, sort with support value, if same then sort with item name
def compare_func(val1, val2):
    global support
    if support[val1] > support[val2]:
        return -1
    elif support[val1] < support[val2]:
        return 1
    else:
        if val1 > val2:
            return -1
        else:
            return 1

def build_tree(data, total, min_support):
    # pointer array
    point = {}
    global support
    for item in support:
        point[item] = []

    # build root node
    index = 0
    root = treeNode(index)
    index += 1
    for t in data:
        # filter items whose support value less than min_support
        t = [item for item in t if float(support[item])/total >= min_support]
        # sort single item order with support value
        t.sort(cmp=compare_func)
        cur = root
        # walk along tree with items
        for item in t:
            flag = False
            for child in cur.child:
                # if item belongs to child nodes
                if child.name == item:
                    child.value += 1
                    cur = child
                    flag = True
                    if cur not in point[item]:
                        point[item].append(cur)
            # create new node
            if flag == False:
                new_node = treeNode(index)
                index += 1
                cur.child.append(new_node)
                new_node.value += 1
                new_node.parent = cur
                new_node.name = item
                cur = new_node
                if cur not in point[item]:
                    point[item].append(cur)

    #show tree node details
    #queue = [root]
    #while len(queue) != 0:
    #    now = queue[0]
    #    print now.index
    #    print now.value
    #    print now.parent
    #    print now.child
    #    print now.name
    #    print '====================='
    #    for x in now.child:
    #        queue.append(x)

    #    del queue[0]
    return root, point

def mining(point, min_support, total):
    global support
    # get all single items support value
    all_items = support.keys()
    all_items.sort(cmp=compare_func)
    all_items.reverse()
    mapping = {}
    # items from smallest support value to  largest support value
    for item in all_items:
        conditional_pattern = {}
        # skip item whose support value less than min_support
        if float(support[item])/total < min_support:
            continue

        values = []
        # trace item on tree to root
        for start in point[item]:
            path = []
            cur = start.parent
            values.append(start.value)
            while cur.index != 0:
                path.append(cur.name)
                cur = cur.parent
            # save path and support value
            conditional_pattern[tuple(path)] = start.value

        count = {}
        # for single item count items in all conditional pattern
        for pattern in conditional_pattern:
            for item in pattern:
                if item not in count:
                    count[item] = conditional_pattern[pattern]
                else:
                    count[item] += conditional_pattern[pattern]
        # remove item that not satisfy min_support
        satisfy_item = [item for item in count if float(count[item])/total >= min_support]
        # trace item again
        for pattern in conditional_pattern:
            path = list(pattern)
            # find out satisfy items on this path
            sets = [x for x in path if x in satisfy_item]
            length = len(sets)
            if length != 0:
                # generate combinations of satisfied items, then each add start node
                for r in range(1, length+1):
                    tmp = list(combinations(sets, r))
                    for x in tmp:
                        if len(x) == 1:
                            x = [x[0]]
                        else:
                            x = list(x)
                        x.append(start.name)
                        if tuple(x) not in mapping:
                            mapping[tuple(x)] = conditional_pattern[pattern]
                        else:
                            mapping[tuple(x)] += conditional_pattern[pattern]
    # filter, make sure all frequent sets satisfy min_support
    remain = {}
    for sets in mapping:
        if float(mapping[sets])/total >= min_support:
            tmp = list(sets)
            tmp.sort(cmp=compare_func)
            remain[tuple(tmp)] = mapping[sets]
    return remain

def generate_rule(L, min_confidence, frequent_support):
    rules = {}
    confidences = {}
    for frequent_set in L:
        # first get largest set's support value
        main_support = frequent_support[tuple(frequent_set)]
        length = len(frequent_set)
        # sets whose parents' set don't satisfy min_confidence
        redundant_set = []
        iter_set = list(combinations(frequent_set, length-1))
        # search form length-1 combinations to single item (top-down)
        for i in range(length-1, 0, -1):
            # remove redundant set from iterative set
            tmp = [item for item in iter_set if item not in redundant_set]
            
            redundant_set = []
            iter_set = []
            for x in tmp:
                if len(x) == 1:
                    x = x[0]
                if type(x) != str:
                    x = list(x)
                    x.sort(cmp=compare_func)
                    x = tuple(x)
                # calculate current set's confidence value
                confidence_value = float(main_support)/frequent_support[tuple(x)]
                # satisfied min_support => rules
                if confidence_value >= min_confidence:
                    rest = [item for item in frequent_set if item not in x]
                    if x not in rules:
                        rules[x] = [rest]
                        confidences[x] = [confidence_value]
                    else:
                        rules[x].append(rest)
                        confidences[x].append(confidence_value)
                    # put subsets into iterative set
                    subsets = list(combinations(x, i-1))
                    for subset in subsets:
                        if subset not in iter_set:
                            iter_set.append(subset)
                # don't satisfied => ignore it's subsets, put into redundant sets
                else:
                    subsets = list(combinations(x, i-1))
                    for subset in subsets:
                        if subset not in redundant_set:
                            redundant_set.append(subset)
            if len(iter_set) == 0:
                break
    return rules, confidences

# compare function for sorting list according to length
def sort_func(val1, val2):
    if len(val1) > len(val2):
        return -1
    return 1

def fp_growth(file_path, argv1, argv2):
    # load data file
    data = loadDataSet(file_path)
    min_support = float(argv1)
    min_confidence = float(argv2)
    # generate L1 set
    tmp_L, count = generate_L1(data, min_support)
    global support
    # save L1 support value in global variable
    for x in count:
        support[x] = count[x]
    # build fp tree
    root, point = build_tree(data, len(data), min_support)
    # mining to find frequent dataset with support value
    frequent_support = mining(point, min_support, len(data))
    L = []
    # sort items order in tuple(set)
    for frequent_set in frequent_support:
        if type(frequent_set) != str:
            tmp = list(frequent_set)
            tmp.sort(cmp=compare_func)
            L.append(tmp)
    # sort frequent sets, larger dataset in front in decreasing order
    L.sort(cmp=sort_func)
    # update single item support value into frequent_support
    for key in support:
        frequent_support[tuple(key)] = support[key]
    # generate rules with frequent sets
    rules, confidences = generate_rule(L, min_confidence, frequent_support)
    sort_dict = {}
    # sort with confidence value, use string as key, confidence value as value
    for left in rules:
        index = 0
        for right in rules[left]:
            tmp_str = str(left) + ' -> ' + str(right) + ' confidence: ' + str(confidences[left][index])
            sort_dict[tmp_str] = confidences[left][index]
            index += 1
    # sort with value
    sort_dict = sorted(sort_dict.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)
    # output association rules
    for result in sort_dict:
        print result[0]

def main():
    if len(sys.argv) != 4:
        print 'Error format. python hw1_fp_growth.py [path_to_file] [min_support] [min_confidence]'
        return
    # command line argument: file path, min_support, min_confidence
    # ex: python hw1_fp_growth.py dataset.data 0.5 0.5
    start = time.time()
    fp_growth(sys.argv[1], sys.argv[2], sys.argv[3])
    end = time.time()
    print 'spend time(s): ', end-start

if __name__ == '__main__':
    main()
