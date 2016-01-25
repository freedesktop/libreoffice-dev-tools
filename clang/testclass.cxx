class S
{
};

class B
{
public:
    B(int, int)
    {
    };

    B(int, S&)
    {
    }
};

class SdrEdgeLineDeltaAnzItem: public B {
public:
    SdrEdgeLineDeltaAnzItem(int nVal=0): B(0,nVal) {}
    SdrEdgeLineDeltaAnzItem(S& rIn);
    virtual B* Clone() const
    {
        return new SdrEdgeLineDeltaAnzItem(*this);
    }

    int GetValue() const
    {
        return 0;
    }
};

SdrEdgeLineDeltaAnzItem::SdrEdgeLineDeltaAnzItem(S& rIn): B(0,rIn)  {}

int main()
{
    SdrEdgeLineDeltaAnzItem* pItem = 0;
    static_cast<const SdrEdgeLineDeltaAnzItem&>(*pItem).GetValue();
    int nValue = static_cast<const SdrEdgeLineDeltaAnzItem*>( 0 )->GetValue();
    return nValue;
}

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
