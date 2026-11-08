# Algorithms for invgal.invariants. The inputs are data records.
IVJson := function(x)
    local i, names, c;
    if x=fail then Error("backend returned fail instead of an exact invariant"); fi;
    if IsStringRep(x) then
        Print("\"");
        for c in x do
            if c='"' then Print("\\\"");
            elif c='\\' then Print("\\\\");
            elif c='\n' then Print("\\n");
            elif c='\r' then Print("\\r");
            elif c='\t' then Print("\\t");
            else Print(String([c])); fi;
        od;
        Print("\"");
    elif IsInt(x) or IsBool(x) then Print(x);
    elif IsRat(x) then IVJson(String(x));
    elif IsList(x) then
        Print("[");
        for i in [1..Length(x)] do
            if i>1 then Print(","); fi;
            IVJson(x[i]);
        od;
        Print("]");
    elif IsRecord(x) then
        names:=SortedList(RecNames(x)); Print("{");
        for i in [1..Length(names)] do
            if i>1 then Print(","); fi;
            IVJson(names[i]); Print(":"); IVJson(x.(names[i]));
        od;
        Print("}");
    else Error("unsupported output type"); fi;
end;

IVHap := function()
    if LoadPackage("hap")=fail then Error("install the GAP HAP package"); fi;
end;

IVSchur := function(G)
    local ans,p;
    if Size(G)>100000 and LoadPackage("cohomolo")<>fail then
        ans:=[];
        for p in Set(FactorsInt(Size(G))) do
            Append(ans,ValueGlobal("SchurMultiplier")(ValueGlobal("CHR")(G,p)));
        od;
        return ans;
    fi;
    IVHap();
    return GroupHomology(G,2);
end;

# Character inner products give the arrows.
# The program does not calculate the full multiplication table of the representation ring.
IVMcKay := function(G,degree,representation)
    local t,irr,classes,values,v,dimension;
    t:=CharacterTable(G); irr:=Irr(t); classes:=ConjugacyClasses(G);
    if representation="regular" then
        values:=List(classes,c->0);
        values[Position(List(classes,c->Order(Representative(c))),1)]:=Size(G);
        dimension:=Size(G);
    elif representation="natural" then
        values:=List(classes,c->Number([1..degree],i->i^Representative(c)=i));
        dimension:=degree;
    else Error("representation must be natural or regular"); fi;
    v:=ClassFunction(t,values);
    return rec(vertex_dimensions:=List(irr,c->c[1]),
        unit_index:=Position(irr,TrivialCharacter(t))-1,
        class_sizes:=SizesConjugacyClasses(t),
        class_orders:=OrdersClassRepresentatives(t),
        character_values:=List(irr,c->List(ValuesOfClassFunction(c),String)),
        arrows:=List(irr,a->List(irr,b->ScalarProduct(v*a,b))),
        representation:=representation,representation_dimension:=dimension,
        representation_character:=List(ValuesOfClassFunction(v),String));
end;

IVCompute := function(G,degree,operation,options)
    local p,d,values,P,R,F,n,classes,c,rep,cycles,terms;
    if operation="betti" then
        IVHap(); p:=options.p; d:=options.max_degree; values:=[1];
        if d>=1 then
            Add(values,Number(AbelianInvariants(G),x->x mod p=0));
        fi;
        if d>=2 then
            P:=SylowSubgroup(G,p);
            R:=ResolutionPrimePowerGroup(P,d+1);
            F:=function(X) return TensorWithIntegersModP(X,p); end;
            for n in [2..d] do
                # Homology and cohomology dimensions agree over a field.
                # PrimePartDerivedFunctor imposes fusion from the full G.
                Add(values,Length(PrimePartDerivedFunctor(G,R,F,n)));
            od;
        fi;
        return values;
    elif operation="schur_multiplier" then
        return IVSchur(G);
    elif operation="bogomolov_multiplier" then
        # Vanishing for abelian groups, and for finite simple groups (Kunyavskii).
        if IsAbelian(G) or IsSimpleGroup(G) then return []; fi;
        IVHap(); return BogomolovMultiplier(G);
    elif operation="molien" then
        classes:=ConjugacyClasses(G); terms:=[];
        for c in classes do
            rep:=Representative(c);
            if options.representation="regular" then
                cycles:=[[Order(rep),Size(G)/Order(rep)]];
            elif options.representation="natural" then
                cycles:=Collected(CycleLengths(rep,[1..degree]));
            else Error("representation must be natural or regular"); fi;
            Add(terms,rec(class_size:=Size(c),cycles:=cycles));
        od;
        return rec(order:=Size(G),terms:=terms);
    elif operation="mckay" then
        return IVMcKay(G,degree,options.representation);
    else Error("unknown invariant operation"); fi;
end;
