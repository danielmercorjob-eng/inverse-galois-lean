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
    local p,d,values,P,R,F,n,classes,c,rep,cycles,terms,
        out,vals,S,periodic,A,subgroups,x,y,factors;
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
    elif operation="integral_cohomology" then
        IVHap(); out:=[];
        for n in options.degrees do
            if n=0 then vals:=[0]; elif n=1 then vals:=[];
            else vals:=GroupCohomology(G,n); fi;
            Add(out,rec(degree:=n,invariants:=vals));
        od;
        return out;
    elif operation="periodicity" then
        if Size(G)=1 then return rec(period:=1,periodic:=true); fi;
        periodic:=true;
        for p in Set(FactorsInt(Size(G))) do
            S:=SylowSubgroup(G,p);
            if not IsCyclic(S) then
                if p<>2 or Sum(List(Filtered(ConjugacyClasses(S),c->Order(Representative(c))=2),Size))<>1
                then periodic:=false; fi;
            fi;
        od;
        if not periodic then return rec(period:="infinity",periodic:=false); fi;
        if IsCyclic(G) then return rec(period:=2,periodic:=true); fi;
        IVHap();
        for d in [1..options.max_period] do
            if d=1 then vals:=[]; else vals:=GroupCohomology(G,d); fi;
            if Product(vals)=Size(G) and IsCyclic(AbelianGroup(vals)) then
                return rec(period:=d,periodic:=true);
            fi;
        od;
        Error("periodic, but least period exceeds max_period");
    elif operation="abelian_structure" then
        if not IsAbelian(G) then return rec(abelian:=false); fi;
        S:=SylowSubgroup(G,options.p);
        return rec(abelian:=true,orders:=List(IndependentGeneratorsOfAbelianGroup(S),Order));
    elif operation="restriction_family" then
        if Size(G)>options.max_elements then Error("restriction family exceeds max_elements"); fi;
        A:=Concatenation([One(G)],Filtered(Elements(G),x->x<>One(G)));
        if options.essential then subgroups:=MaximalSubgroups(G);
        else
            subgroups:=List(options.subgroups,gs->Group(
                Concatenation([One(G)],List(gs,perm->PermList(List(perm,x->x+1))))));
        fi;
        if Length(subgroups)>options.max_subgroups then Error("restriction family exceeds max_subgroups"); fi;
        for S in subgroups do
            if not IsSubgroup(G,S) then Error("a detection subgroup is not contained in G"); fi;
        od;
        return List(subgroups,S->List(Filtered(A,x->x in S),x->Position(A,x)-1));
    elif operation="cyclic_sylow" then
        p:=options.p; S:=SylowSubgroup(G,p);
        if not IsCyclic(S) then return rec(cyclic:=false,order:=Size(S)); fi;
        return rec(cyclic:=true,order:=Size(S),
            automizer:=Size(Normalizer(G,S))/Size(Centralizer(G,S)));
    elif operation="factor_polynomial" then
        A:=UnivariatePolynomial(Rationals,options.coefficients);
        factors:=Collected(Factors(A));
        return List(factors,x->rec(coefficients:=CoefficientsOfUnivariatePolynomial(x[1]),multiplicity:=x[2]));
    elif operation="finite_model" then
        if Size(G)>options.max_elements then Error("finite_model exceeds max_elements"); fi;
        A:=Concatenation([One(G)],Filtered(Elements(G),x->x<>One(G)));
        return rec(table:=List(A,x->List(A,y->Position(A,x*y)-1)),
            elements:=List(A,x->List([1..degree],i->i^x)));
    else Error("unknown invariant operation"); fi;
end;
