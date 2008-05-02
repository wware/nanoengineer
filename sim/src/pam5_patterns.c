// Copyright 2007 Nanorex, Inc.  See LICENSE file for details. 

#include "simulator.h"

static char const rcsid[] = "$Id$";

static char *
trace_atomID(struct atom *a)
{
  static char buf[16];
  if (a == NULL) {
    return "x";
  }
  if (a->virtualConstructionAtoms != 0) {
    sprintf(buf, "{%d}", a->atomID);
  } else {
    sprintf(buf, "%d", a->atomID);
  }
  return buf;
}

static void
trace_makeBond(struct patternMatch *match, struct bond *b)
{
  char buf[1024];
  char buf1[64];
  struct bondStretch *stretchType;

  sprintf(buf, "# Pattern makeBond: [%d] %s ", match->sequenceNumber, trace_atomID(b->a1));
  strcat(buf, trace_atomID(b->a2));

  stretchType = getBondStretch(b->a1->type->protons,
                               b->a2->type->protons,
                               b->order);

  sprintf(buf1, " %f %f\n", stretchType->ks, stretchType->r0);
  
  strcat(buf, buf1);
  write_traceline(buf);
}

static void
trace_makeVirtualAtom(struct patternMatch *match, struct atom *a)
{
  char buf[1024];
  char buf1[64];

  sprintf(buf, "# Pattern makeVirtualAtom: [%d] %s %d %d ",
          match->sequenceNumber,
          trace_atomID(a),
          a->virtualConstructionAtoms,
          a->virtualFunction);
  strcat(buf, trace_atomID(a->creationParameters.v.virtual1));
  strcat(buf, " ");
  strcat(buf, trace_atomID(a->creationParameters.v.virtual2));
  strcat(buf, " ");
  strcat(buf, trace_atomID(a->creationParameters.v.virtual3));
  strcat(buf, " ");
  strcat(buf, trace_atomID(a->creationParameters.v.virtual4));
  sprintf(buf1, " %f %f %f\n",
          a->creationParameters.v.virtualA,
          a->creationParameters.v.virtualB,
          a->creationParameters.v.virtualC);
  strcat(buf, buf1);
  write_traceline(buf);
}

static void
trace_setStretchType(struct patternMatch *match, struct stretch *s)
{
  char buf[1024];
  char buf1[64];

  sprintf(buf, "# Pattern setStretchType: [%d] %s ", match->sequenceNumber, trace_atomID(s->a1));
  strcat(buf, trace_atomID(s->a2));
  sprintf(buf1, " %f %f\n", s->stretchType->ks, s->stretchType->r0);
  strcat(buf, buf1);
  write_traceline(buf);
}


static void
pam5_requires_gromacs(struct part *p)
{
  if (GromacsOutputBaseName == NULL) {
    ERROR("PAM5 DNA structures must be minimized with GROMACS");
    p->parseError(p->stream);
  }
}

// The three vectors from aAx1 to the other three atoms can be thought
// of as the basis for a coordinate system.  We would like that
// coordinate system to be right handed, and we return true if that is
// the case.  If not, swapping aSa and aSb would form a right hand
// system.
static int
isExpectedTwist(struct part *p,
                struct atom *aAx1,
                struct atom *aAx2,
                struct atom *aSa,
                struct atom *aSb)
{
  struct xyz v0;
  struct xyz v1;
  struct xyz v2;
  struct xyz v3;
  struct xyz v1_x_v2;

  if (aAx1->virtualConstructionAtoms ||
      aAx2->virtualConstructionAtoms ||
      aSa->virtualConstructionAtoms ||
      aSb->virtualConstructionAtoms)
  {
    return 0;
  }
  v0 = p->positions[aAx1->index];
  v1 = p->positions[aAx2->index];
  v2 = p->positions[aSa->index];
  v3 = p->positions[aSb->index];
  vsub(v1, v0);
  vsub(v2, v0);
  vsub(v3, v0);
  v2x(v1_x_v2, v1, v2);
  return vdot(v1_x_v2, v3) > 0.0;
}

static int stack_match_initialized = 0;
static double vDax_p[8];
static double vDax_q[8];
static double vDbx_p[8];
static double vDbx_q[8];
static struct atomType *vDa_type[8];
static struct atomType *vDb_type[8];

static struct bondStretch *stretch_5_Pl_Ss_3;
static struct bondStretch *stretch_5_Ss_Pl_3;


static void
init_stack_match(void)
{
  int i;
  char buf[256];
  struct patternParameter *param;
  double r0;
  double ks;

  if (stack_match_initialized) {
    return;
  }
  for (i=0; i<8; i++) {
    sprintf(buf, "vDa%d", i+1);
    vDa_type[i] = getAtomTypeByName(buf);
    sprintf(buf, "vDb%d", i+1);
    vDb_type[i] = getAtomTypeByName(buf);

    sprintf(buf, "PAM5-Stack:vDa%d-p", i+1);
    param = getPatternParameter(buf); BAIL();
    vDax_p[i] = param->value;
    sprintf(buf, "PAM5-Stack:vDa%d-q", i+1);
    param = getPatternParameter(buf); BAIL();
    vDax_q[i] = param->value;
    sprintf(buf, "PAM5-Stack:vDb%d-p", i+1);
    param = getPatternParameter(buf); BAIL();
    vDbx_p[i] = param->value;
    sprintf(buf, "PAM5-Stack:vDb%d-q", i+1);
    param = getPatternParameter(buf); BAIL();
    vDbx_q[i] = param->value;
  }
  param = getPatternParameter("PAM5:5-Pl-Ss-3_r0"); BAIL();
  r0 = param->value; // pm
  param = getPatternParameter("PAM5:5-Pl-Ss-3_ks"); BAIL();
  ks = param->value; // N/m
  stretch_5_Pl_Ss_3 = newBondStretch("5-Pl-Ss-3", ks, r0, 1.0, -1.0, -1.0, 9, 1);

  param = getPatternParameter("PAM5:5-Ss-Pl-3_r0"); BAIL();
  r0 = param->value; // pm
  param = getPatternParameter("PAM5:5-Ss-Pl-3_ks"); BAIL();
  ks = param->value; // N/m
  stretch_5_Ss_Pl_3 = newBondStretch("5-Ss-Pl-3", ks, r0, 1.0, -1.0, -1.0, 9, 1);

  stack_match_initialized = 1;
}

static void
pam5_basepair_match(struct patternMatch *match)
{
  struct atom *aS1 = match->p->atoms[match->atomIndices[1]];
  struct atom *aS2 = match->p->atoms[match->atomIndices[2]];
  struct bond *bond;

  pam5_requires_gromacs(match->p); BAIL();
  init_stack_match();
  bond = makeBond(match->p, aS1, aS2, '1');
  queueBond(match->p, bond);
  trace_makeBond(match, bond);
  //printMatch(match);
}

static void
pam5_stack_match(struct patternMatch *match)
{
  struct atom *aGv1 = match->p->atoms[match->atomIndices[0]];
  struct atom *aGv2 = match->p->atoms[match->atomIndices[1]];
  struct atom *aS1a = match->p->atoms[match->atomIndices[2]];
  struct atom *aS1b = match->p->atoms[match->atomIndices[3]];
  struct atom *aS2a = match->p->atoms[match->atomIndices[4]];
  struct atom *aS2b = match->p->atoms[match->atomIndices[5]];
  struct atom *vA;
  struct atom *vB;
  struct bond *bond;
  int i;
  
  pam5_requires_gromacs(match->p); BAIL();
  init_stack_match();
  
  // S1a    S2b
  //  |      |
  // Gv1----Gv2
  //  |      |
  // S1b    S2a
  if (!isExpectedTwist(match->p, aGv1, aGv2, aS1a, aS1b)) {
    aS1a = match->p->atoms[match->atomIndices[3]];
    aS1b = match->p->atoms[match->atomIndices[2]];
  }
  if (!isExpectedTwist(match->p, aGv2, aGv1, aS2a, aS2b)) {
    aS2a = match->p->atoms[match->atomIndices[5]];
    aS2b = match->p->atoms[match->atomIndices[4]];
  }
  // Atoms are now in canonical orientations.  The twist is such that
  // the S1a-S2a distance is greater than the S1b-S2b distance in
  // BDNA.
  for (i=0; i<8; i++) {
    vA = makeVirtualAtom(vDa_type[i], sp3, 3, 1,
                         aGv1, aS1a, aS1b, NULL,
                         vDax_p[i], vDax_q[i], 0.0);
    vB = makeVirtualAtom(vDb_type[i], sp3, 3, 1,
                         aGv2, aS2a, aS2b, NULL,
                         vDbx_p[i], vDbx_q[i], 0.0);
    bond = makeBond(match->p, vA, vB, '1');
    queueAtom(match->p, vA);
    trace_makeVirtualAtom(match, vA);
    queueAtom(match->p, vB);
    trace_makeVirtualAtom(match, vB);
    queueBond(match->p, bond);
    trace_makeBond(match, bond);
  }
  //printMatch(match);
}

// Sets the phosphate-sugar bond type differently based on the bond
// direction.  This allows the phosphate to be closer to one sugar
// than the other, based on the strand direction.
static void
pam5_phosphate_sugar_match(struct patternMatch *match) 
{
  struct part *p = match->p;
  struct atom *aPl = p->atoms[match->atomIndices[0]];
  struct atom *aSs = p->atoms[match->atomIndices[1]];
  struct bond *b = getBond(p, aPl, aSs); BAIL();
  struct stretch *s = getStretch(p, aPl, aSs); BAIL();
  int reverse;

  pam5_requires_gromacs(match->p); BAIL();
  init_stack_match();

  switch (b->direction) {
  case 'F':
    reverse = (b->a1 == aSs);
    break;
  case 'R':
    reverse = (b->a1 == aPl);
    break;
  default:
    ERROR2("pam5_phosphate_sugar_match: bond between ids %d and %d has no direction", aPl->atomID, aSs->atomID);
    p->parseError(p->stream);
    return;
  }
  s->stretchType = reverse ? stretch_5_Ss_Pl_3 : stretch_5_Pl_Ss_3 ;
  trace_setStretchType(match, s);
  //printMatch(match);
}

// Creates the Pl-Pl interaction, which replaces the Pl-Ss-Pl bend
// term.
static void
pam5_phosphate_phosphate_match(struct patternMatch *match) 
{
  struct part *p = match->p;
  struct atom *aPl1 = p->atoms[match->atomIndices[0]];
  struct atom *aPl2 = p->atoms[match->atomIndices[2]];
  struct bond *bond;
  
  pam5_requires_gromacs(p); BAIL();

  bond = makeBond(p, aPl1, aPl2, '1');
  queueBond(p, bond);
  trace_makeBond(match, bond);
  //printMatch(match);
}

// Creates the Gv-Pl interaction, which replaces the Gv-Ss-Pl bend
// term.  Only do this on the 5' side.
static void
pam5_groove_phosphate_match(struct patternMatch *match)
{
  struct part *p = match->p;
  struct atom *aGv = p->atoms[match->atomIndices[0]];
  struct atom *aSs = p->atoms[match->atomIndices[1]];
  struct atom *aPl = p->atoms[match->atomIndices[2]];
  struct bond *b = getBond(p, aPl, aSs); BAIL();
  struct bond *bond;
  int reverse;

  pam5_requires_gromacs(p); BAIL();

  switch (b->direction) {
  case 'F':
    reverse = (b->a1 == aSs);
    break;
  case 'R':
    reverse = (b->a1 == aPl);
    break;
  default:
    ERROR2("pam5_phosphate_sugar_match: bond between ids %d and %d has no direction", aPl->atomID, aSs->atomID);
    p->parseError(p->stream);
    return;
  }
  if (reverse) {
    return;
  }
  
  bond = makeBond(p, aPl, aGv, '1');
  queueBond(p, bond);
  trace_makeBond(match, bond);
  //printMatch(match);
}

void
createPam5Patterns(void)
{
  struct compiledPatternTraversal *t[10];
  struct compiledPatternAtom *a[10];

  if (VanDerWaalsCutoffRadius < 0.0) {
    // this indicates that the model has no pam5 atoms
    return;
  }
  stack_match_initialized = 0;
  
  a[0] = makePatternAtom(0, "P5G");
  a[1] = makePatternAtom(1, "P5S");
  a[2] = makePatternAtom(2, "P5S");
  t[0] = makeTraversal(a[0], a[1], '1');
  t[1] = makeTraversal(a[0], a[2], '1');
  makePattern("PAM5-basepair", pam5_basepair_match, 3, 2, t);

  a[0] = makePatternAtom(0, "P5G");
  a[1] = makePatternAtom(1, "P5G");
  a[2] = makePatternAtom(2, "P5S");
  a[3] = makePatternAtom(3, "P5S");
  a[4] = makePatternAtom(4, "P5S");
  a[5] = makePatternAtom(5, "P5S");
  t[0] = makeTraversal(a[0], a[1], '1');
  t[1] = makeTraversal(a[0], a[2], '1');
  t[2] = makeTraversal(a[0], a[3], '1');
  t[3] = makeTraversal(a[1], a[4], '1');
  t[4] = makeTraversal(a[1], a[5], '1');
  makePattern("PAM5-stack", pam5_stack_match, 6, 5, t);

  a[0] = makePatternAtom(0, "P5P");
  a[1] = makePatternAtom(1, "P5S");
  t[0] = makeTraversal(a[0], a[1], '1');
  makePattern("PAM5-phosphate-sugar", pam5_phosphate_sugar_match, 2, 1, t);

  a[0] = makePatternAtom(0, "P5P");
  a[1] = makePatternAtom(1, "P5S");
  a[2] = makePatternAtom(2, "P5P");
  t[0] = makeTraversal(a[0], a[1], '1');
  t[1] = makeTraversal(a[1], a[2], '1');
  makePattern("PAM5-phosphate-phosphate", pam5_phosphate_phosphate_match, 3, 2, t);

  a[0] = makePatternAtom(0, "P5G");
  a[1] = makePatternAtom(1, "P5S");
  a[2] = makePatternAtom(2, "P5P");
  t[0] = makeTraversal(a[0], a[1], '1');
  t[1] = makeTraversal(a[1], a[2], '1');
  makePattern("PAM5-groove-phosphate", pam5_groove_phosphate_match, 3, 2, t);
}
