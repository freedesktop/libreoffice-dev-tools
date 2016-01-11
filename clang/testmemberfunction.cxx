namespace ns
{
class C
{
public:
    void foo(int x);
};
}

void ns::C::foo(int /*x*/)
{
}

int main(int /*argc*/, char** /*argv*/)
{
    ns::C aC;
    aC.foo(0);
}

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
