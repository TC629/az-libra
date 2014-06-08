#ifndef QUEUE_HPP
#define QUEUE_HPP

// Nodo para una lista doblemente enlazada.
template <typename T>
struct QueueNode {

    T val;
    QueueNode* next;
    QueueNode* prev;

    QueueNode() {

        next = 0;
        prev = 0;
    }

    QueueNode(const T val, QueueNode* next=0, QueueNode* prev=0) {

        this->val = val; // requiere constructor por copia
        this->next = next;
        this->prev = prev;
    }
};

// Lista doblemente enlazada con interfaz de cola. 
template <typename T>
class Queue {

    public:

        // Constructor.
        Queue() : _size(0) {
        
            sentinel = new QueueNode<T>();
            sentinel->next = sentinel;
            sentinel->prev = sentinel;
        }

        // Destructor.
        ~Queue() {
            
            QueueNode<T>* node = sentinel;
            QueueNode<T>* target;

            while((target = node->next) != sentinel) {

                node->next = target->next; 
                delete target;
            }

            delete sentinel;
        }

        // Encola un elemento.
        void enqueue(const T val) {

            QueueNode<T>* newNode = new QueueNode<T>(val);

            newNode->prev = sentinel->prev; 
            sentinel->prev->next = newNode;

            sentinel->prev = newNode;
            newNode->next = sentinel;
            _size++;
        }

        // Desencola un elemento.
        T dequeue() {

            T val;
            if(_size > 0) {
                QueueNode<T>* node = sentinel->next;
                sentinel->next = node->next;
                sentinel->next->prev = sentinel;

                val = node->val;
                delete node;
                _size--;
            }

            return val;
        }

        int size() const { return _size; }

    private:

        QueueNode<T>* sentinel;
        int _size;
};

#endif
