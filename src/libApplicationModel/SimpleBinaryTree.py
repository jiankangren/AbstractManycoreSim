# simple binary tree
# in this implementation, a node is inserted between an existing node and the root


class BinaryTree():

    def __init__(self,rootid):
        self.left = None
        self.right = None
        self.rootid = rootid

    def getLeftChild(self):
        return self.left
    def getRightChild(self):
        return self.right
    def setNodeValue(self,value):
        self.rootid = value
    def getNodeValue(self):
        return self.rootid

    def insertRight(self,newNode):
        if self.right == None:
            self.right = BinaryTree(newNode)
        else:
            tree = BinaryTree(newNode)
            tree.right = self.right
            self.right = tree
        
    def insertLeft(self,newNode):
        if self.left == None:
            self.left = BinaryTree(newNode)
        else:
            tree = BinaryTree(newNode)
            self.left = tree
            tree.left = self.left
    
    # try to insert to left, if not insert to right
    def insert(self, newNode, max_depth, current_depth=0):
        if self.left == None:
            self.left = BinaryTree(newNode)
        else:
            if(current_depth < max_depth):
                current_depth+=1
                self.left.insert(newNode, max_depth, current_depth)
            else:
                if(self.right == None):
                    self.right = BinaryTree(newNode)
                else:
                    
                
                
            
        
    
'''
    def insert(item, tree):
        if (item < tree.entry):
            if (tree.left != None):
                insert(item, tree.left)
            else:
                tree.left = Tree(item)
        else:
            if (tree.right != None):
                insert(item, tree.right)
            else:
                tree.right = Tree(item)

'''

def printTree(tree):
        if tree != None:
            printTree(tree.getLeftChild())
            print(tree.getNodeValue())
            printTree(tree.getRightChild())
            


# test tree

def testTree():
    myTree = BinaryTree("Maud")
    myTree.insertLeft("Bob")
    myTree.insertRight("Tony")
    myTree.insertRight("Steven")
    printTree(myTree)
        
testTree()